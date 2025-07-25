from django.contrib.auth.decorators import login_required

# Update cart item quantity
@login_required
def update_cart(request, item_id):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()
        except ValueError:
            pass
    return redirect('cart')

# Remove cart item
@login_required
def remove_from_cart(request, item_id):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    if request.method == 'POST':
        cart_item.delete()
    return redirect('cart')
from django.shortcuts import render, redirect, get_object_or_404
from catalog.models import Product, Cart, CartItem

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pr_id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
    )
    if created:
        cart_item.quantity = 1
    else:
        cart_item.quantity += 1
    cart_item.save()
    return redirect('cart')


@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    return render(request, 'cart.html', {'cart_items': cart_items})
# ...existing code...