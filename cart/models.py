from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product
# Create your models here.

#  ...existing code...
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
# ...existing code...