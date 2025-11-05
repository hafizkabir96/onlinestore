# cart/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Cart, CartItem
from products.models import Product
from vendors.models import Vendor   # <-- make sure Vendor is imported


# ----------------------------------------------------------------------
# Helper – get (or create) the correct cart for the current vendor
# ----------------------------------------------------------------------
def _get_cart(request, vendor):
    if not request.session.session_key:
        request.session.create()
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user, vendor=vendor)
    else:
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key, vendor=vendor)
    request.session['cart_id'] = cart.id
    return cart


# ----------------------------------------------------------------------
# 1. View Cart
# ----------------------------------------------------------------------
def view_cart(request, vendor_slug):
    vendor = get_object_or_404(Vendor, slug=vendor_slug)
    cart   = _get_cart(request, vendor)

    # Suggested products (exclude items already in cart)
    suggested = Product.objects.filter(vendor=vendor)\
                    .exclude(id__in=[i.product.id for i in cart.items.all()])[:4]

    context = {
        'cart': cart,
        'vendor': vendor,
        'suggested_products': suggested,
        'year': timezone.now().year,
    }
    return render(request, 'cart/cart.html', context)


# ----------------------------------------------------------------------
# 2. Add to Cart (AJAX + normal POST)
# ----------------------------------------------------------------------
@require_POST
def add_to_cart(request, product_id, vendor_slug):
    product = get_object_or_404(Product, id=product_id)
    cart    = _get_cart(request, product.vendor)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()

    # ----- AJAX response ------------------------------------------------
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        total_items = sum(i.quantity for i in cart.items.all())
        return JsonResponse({
            'success': True,
            'message': f'Added {product.name}',
            'cart_count': total_items,
            'subtotal': item.subtotal(),
        })

    messages.success(request, f'Added {product.name}')
    return redirect('cart:view_cart', vendor_slug=vendor_slug)


# ----------------------------------------------------------------------
# 3. Update Cart (increase / decrease)
# ----------------------------------------------------------------------
@require_POST
def update_cart(request, item_id, vendor_slug):
    item = get_object_or_404(CartItem, id=item_id)
    action = request.POST.get('action')

    if action == 'increase':
        item.quantity += 1
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
        else:
            item.delete()
            return JsonResponse({'removed': True})

    item.save()
    return JsonResponse({
        'quantity': item.quantity,
        'subtotal': item.subtotal(),
    })


# ----------------------------------------------------------------------
# 4. Remove from Cart
# ----------------------------------------------------------------------
@require_POST
def remove_from_cart(request, item_id, vendor_slug):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    return JsonResponse({'success': True})


# ----------------------------------------------------------------------
# 5. **CHECKOUT PAGE** (the missing view)
# ----------------------------------------------------------------------
def checkout(request, vendor_slug):
    vendor = get_object_or_404(Vendor, slug=vendor_slug)
    cart   = _get_cart(request, vendor)

    # If cart is empty → go back to cart
    if not cart.items.exists():
        messages.info(request, "Your cart is empty.")
        return redirect('cart:view_cart', vendor_slug=vendor_slug)

    context = {
        'cart': cart,
        'vendor': vendor,
        'year': timezone.now().year,
    }
    return render(request, 'cart/checkout.html', context)


# ----------------------------------------------------------------------
# 6. Cart-Count API (used by base.html for live count)
# ----------------------------------------------------------------------
def cart_count_api(request, vendor_slug):
    """Return JSON with the current total quantity in the cart."""
    if 'cart_id' not in request.session:
        return JsonResponse({'cart_count': 0})

    try:
        cart = Cart.objects.get(id=request.session['cart_id'])
        total = sum(i.quantity for i in cart.items.all())
        return JsonResponse({'cart_count': total})
    except Cart.DoesNotExist:
        return JsonResponse({'cart_count': 0})