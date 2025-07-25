from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product, UserProfile, Cart, Wishlist, Order, CartItem, OrderedItem
from .forms import UserProfileForm
import random

def home(request):
    """Home/Landing page"""
    all_products = list(Product.objects.all())
    if len(all_products) > 8:
        products = random.sample(all_products, 8)
    else:
        products = all_products
        
    context = {
        'products': products,
    }
    return render(request, 'catalog/home.html', context)

def signup(request):
    """User registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            # Create cart for user
            Cart.objects.create(user=user)
            # Create wishlist for user
            Wishlist.objects.create(user=user)
            
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'catalog/signup.html', {'form': form})

def user_login(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'catalog/login.html')

@login_required
def user_logout(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def profile(request):
    """User profile page"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    context = {
        'user_profile': user_profile,
        'form': form,
    }
    return render(request, 'catalog/profile.html', context)

def product_list(request):
    """Product catalog with filtering"""
    products = Product.objects.all()
    
    # Filtering
    category = request.GET.get('category')
    season = request.GET.get('season')
    fabric = request.GET.get('fabric')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    brand = request.GET.get('brand')
    
    if category:
        products = products.filter(pr_cate=category)
    if season:
        products = products.filter(pr_season=season)
    if fabric:
        products = products.filter(pr_fabric__icontains=fabric)
    if price_min:
        products = products.filter(pr_price__gte=price_min)
    if price_max:
        products = products.filter(pr_price__lte=price_max)
    if brand:
        products = products.filter(pr_brand__icontains=brand)
    
    context = {
        'products': products,
        'categories': Product.CATEGORY_CHOICES,
        'seasons': Product.SEASON_CHOICES,
    }
    return render(request, 'catalog/product_list.html', context)

def product_detail(request, product_id):
    """Product detail page"""
    product = get_object_or_404(Product, pr_id=product_id)
    # If you have a Review model, use: reviews = Review.objects.filter(product=product).order_by('-created_at')
    reviews = []
    
    context = {
        'product': product,
        'reviews': reviews,
    }
    return render(request, 'catalog/product_detail.html', context)

@login_required
def add_to_cart(request, product_id):
    """Add product to cart (with quantity)"""
    product = get_object_or_404(Product, pr_id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()
    messages.success(request, f'{product.pr_name} added to cart!')
    return redirect('cart')

@login_required
def cart(request):
    """View cart and update quantities"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('product')
    total = sum(item.product.pr_price * item.quantity for item in cart_items)
    if request.method == 'POST':
        for item in cart_items:
            qty = int(request.POST.get(f'quantity_{item.pk}', item.quantity))
            if qty > 0:
                item.quantity = qty
                item.save()
            else:
                item.delete()
        messages.success(request, 'Cart updated!')
        return redirect('cart')
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'catalog/cart.html', context)
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

# Checkout view
@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        # Update user profile
        user_profile.address = address
        user_profile.phone = phone
        user_profile.save()
        # Create OrderedItems and Order
        ordered_items = []
        total_price = 0
        for item in cart_items:
            ordered_item = OrderedItem.objects.create(
                product=item.product,
                quantity=item.quantity,
                price=item.product.pr_price
            )
            ordered_items.append(ordered_item)
            total_price += item.product.pr_price * item.quantity
        order = Order.objects.create(
            user=request.user,
            total_price=total_price
        )
        order.items.set(ordered_items)
        order.save()
        # Clear cart
        cart_items.delete()
        messages.success(request, 'Order placed successfully!')
        return redirect('profile')
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    """Remove an item from the cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')

@login_required
def wishlist(request):
    """User wishlist"""
    user_wishlist = get_object_or_404(Wishlist, user=request.user)
    context = {
        'wishlist': user_wishlist,
    }
    return render(request, 'catalog/wishlist.html', context)

@login_required
def add_to_wishlist(request, product_id):
    """Add product to wishlist"""
    product = get_object_or_404(Product, pr_id=product_id)
    user_wishlist = get_object_or_404(Wishlist, user=request.user)
    user_wishlist.products.add(product)
    messages.success(request, f'{product.pr_name} added to wishlist!')
    return redirect('product_detail', product_id=product_id)
