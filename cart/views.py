from django.shortcuts import redirect, get_object_or_404
from catalog.models import Product
from .models import CartItem

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
    )
    cart_item.quantity += 1
    cart_item.save()
    return redirect('cart_detail')


def cart_detail(request):
    cart_items = CartItem.objects.filter(user=request.user)
    return render(request, 'cart.html', {'cart_items': cart_items})
# ...existing code...