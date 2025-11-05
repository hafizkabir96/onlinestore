# orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from .models import Order, OrderItem
from cart.models import Cart
from django.views.decorators.http import require_POST

def checkout_page(request):
    if not getattr(request, "is_vendor_subdomain", False):
        raise Http404("Checkout only on vendor stores")
    vendor = request.vendor
    # fetch cart
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, vendor=vendor).first()
    else:
        session_key = request.session.session_key
        cart = Cart.objects.filter(session_key=session_key, vendor=vendor).first()
    if not cart or not cart.items.exists():
        return redirect("view_cart")
    if request.method == "POST":
        # gather customer details
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        email = request.POST.get("email")
        total_cents = int(cart.total_price() * 100)
        order = Order.objects.create(vendor=vendor, customer_name=name, customer_phone=phone,
                                     customer_address=address, customer_email=email, total_cents=total_cents)
        for item in cart.items.all():
            OrderItem.objects.create(order=order, product=item.product, product_name=item.product.name,
                                     unit_price_cents=int(item.product.price * 100), quantity=item.quantity)
        # clear cart
        cart.delete()
        return render(request, "orders/thankyou.html", {"order": order})
    return render(request, "orders/checkout.html", {"cart": cart, "vendor": vendor})