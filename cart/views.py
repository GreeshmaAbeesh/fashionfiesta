from django.shortcuts import render,redirect,get_object_or_404
from storeitem.models import PopularProduct,Variation,ProductOffer
from orders.models import Wallet,OrderProduct
from category.models import Category
from .models import Cart,CartItem
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import F
from django.db.models import Count

from django.utils import timezone
#from .models import ProductOffer
# Create your views here.


def _cart_id(request):                  # cart made as private
    cart = request.session.session_key  # inside cookies there is session and it gives session id.
    if not cart:                        # if there is no asession, it will create new session
        cart = request.session.create()
    return cart                         # here return the cart id

# we get the product here

def add_cart(request,product_id):
    product=PopularProduct.objects.get(id=product_id)  # to get the product
    # we get product variation here
    product_variation = []          # inside this list we have color and size
    if request.method == 'POST':
        #quantity = int(request.POST.get('quantity',1))
        for item in request.POST:
            key = item            # if color is black,color will stored in the key
            value = request.POST[key]   # black is stored in the value
            
            #to check the match of variation category in model and value

            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key,variation_value__iexact=value)
                print('inside add cart',variation)
                product_variation.append(variation)  # here insert values to a cart item
            except:
                pass
        
   
    #we get cart
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request)) #here  it will match cart id with session id. get the cart using the cart_id. [ we need to cart id from session.ie inside cookies there is session and it gives session id.. that session is taken as cart id]
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id =_cart_id(request)
        )
    cart.save()

    #we get cartitem
    print("above is cartitem exist")
    print('cart,user,product',cart,request.user,product)
    is_cart_item_exists = CartItem.objects.filter(product=product,cart=cart,user=request.user).exists()
    if is_cart_item_exists:
        print("inside is cartitem exist")
        cart_item = CartItem.objects.filter(product=product,cart=cart,user=request.user)      # return cart item objects
        #existing variations from database
        #current variations in product_variation list
        # item_id from database
        ex_var_list = []
        id = []
        for item in cart_item:    #check weather the current variation inside exsting variation then increase quantity of item
            existing_variation = item.variations.all()
            ex_var_list.append(list(existing_variation))
            id.append(item.id)

        print(ex_var_list)

        if product_variation in ex_var_list:
            # increase the cart item quantity
            index =  ex_var_list.index(product_variation)
            item_id = id[index]
            item = CartItem.objects.get(product=product, id=item_id)
            item.quantity += 1
            item.save()
        
        else:
            #create new cart item
            item = CartItem.objects.create(product=product, quantity=1, cart=cart,user=request.user)
            if len(product_variation)>0:   #if product variation list not empty
                item.variations.clear()
                item.variations.add(*product_variation) 
            item.save()

    else:
        cart_item = CartItem.objects.create(
            product = product,
            quantity = 1,      # 1 because it is new cartitem
            cart  = cart,
            user = request.user,
        )
        if len(product_variation)>0:   #if product variation in empty list
            cart_item.variations.clear()
            cart_item.variations.add(*product_variation)
        cart_item.save()
    return redirect('cart')

'''
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    # Your code to render the cart items goes here 
    print('cart_items:',cart_items)
    return render(request, 'store/cart.html', {'cart_items': cart_items})
'''

def remove_cart(request, product_id,cart_item_id):                        # this function is used to reduce cart item while clicking minus button
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(PopularProduct,id=product_id)
    try:
        cart_item = CartItem.objects.get(product=product , cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')



def remove_cart_item(request, product_id,cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(PopularProduct,id=product_id)        
    cart_item = CartItem.objects.get(product=product , cart=cart,id=cart_item_id)
    cart_item.delete()
    return redirect('cart')


'''
def apply_offers(product):
    try:
        offer = ProductOffer.objects.filter(product=product, start_date__lte=timezone.now(), end_date__gte=timezone.now()).first()
        if offer:
            return product.price * (1 - (offer.discount_percentage / 100))
        else:
            return product.price
    except ProductOffer.DoesNotExist:
        return product.price
'''    

        
    
def cart(request, total=0, quantity=0, cart_items=None):           # to modify cart function and add items to cart
    try:
        tax = 0
        grand_total = 0
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart,is_active=True).order_by(F('product__price').asc()) 
        
        for cart_item in cart_items:
            # Apply product offer if available
            product = cart_item.product
            offer = ProductOffer.objects.filter(product=product, start_date__lte=timezone.now(), end_date__gte=timezone.now()).first()
            if offer:
                total += (product.price * (1 - (offer.discount_percentage / 100)) * cart_item.quantity)
                product.price = product.price-(product.price*(offer.discount_percentage / 100))
            else:
                total += (product.price * cart_item.quantity)
                #total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass 

    context = {
        'total' : total,
        'quantity' : quantity,
        'cart_items' : cart_items,
        'tax' : tax ,
        'grand_total' : grand_total,
    }
    return render(request,'store/cart.html',context)   




@login_required(login_url='login')
def checkout(request,total=0, quantity=0, cart_items=None):
   # wallet = Wallet.objects.get(id=wallet_id)
    try:
        tax = 0
        grand_total = 0
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart,is_active=True)
        for cart_item in cart_items:
            # Apply product offer if available
            product = cart_item.product
            offer = ProductOffer.objects.filter(product=product, start_date__lte=timezone.now(), end_date__gte=timezone.now()).first()
            if offer:
                total += (product.price * (1 - (offer.discount_percentage / 100)) * cart_item.quantity)
                product.price = product.price-(product.price*(offer.discount_percentage / 100))
            else:
                total += (product.price * cart_item.quantity)
                #total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass 

    context = {
        'total' : total,
        'quantity' : quantity,
        'cart_items' : cart_items,
        'tax' : tax ,
        'grand_total' : grand_total,
        #'wallet' : wallet,
    }
    return render(request,'store/checkout.html',context)

'''
def get_best_selling_products():
    """
    Get the top 10 best-selling products
    """
    best_selling_products = OrderProduct.objects.values('product').annotate(total_sales=Count('product')).order_by('-total_sales')[:10]
    product_ids = [item['product'] for item in best_selling_products]
    return PopularProduct.objects.filter(id__in=product_ids)

def get_best_selling_categories():
    """
    Get the top 10 best-selling categories
    """
    best_selling_categories = OrderProduct.objects.values('product__category').annotate(total_sales=Count('product__category')).order_by('-total_sales')[:10]
    category_ids = [item['product__category'] for item in best_selling_categories]
    return Category.objects.filter(id__in=category_ids)

'''