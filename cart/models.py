from django.db import models
from storeitem .models import PopularProduct,Variation
from accounts .models import Account
from coupons .models import Coupon

# Create your models here.

class Cart(models.Model):
    cart_id    = models.CharField(max_length=250,blank=True)
    date_added = models.DateField(auto_now_add=True)
    coupons = models.ManyToManyField(Coupon, blank=True)

    def __str__(self):
        return self.cart_id
    

class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE,null=True)
    product = models.ForeignKey(PopularProduct, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    cart    = models.ForeignKey(Cart, on_delete=models.CASCADE,null=True)
    quantity = models.IntegerField()
    order_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        return self.product.price * self.quantity  #here self.product.price means inside CartItem-product-price in PopularProduct using foreign key  * quantity od item in  CartItem-

    def __unicode__(self):
        return self.product