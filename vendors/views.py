# vendors/views.py
from django.shortcuts import render, redirect, get_object_or_404 
from django.urls import reverse
import re
from django.views.decorators.cache import never_cache
import urllib.parse

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Vendor
from .forms import ProductForm
from products.models import Product , Category
from cart.models import Cart, CartItem
from orders.models import Order
from django.http import Http404
from django.core.paginator import Paginator
from datetime import datetime
from django.db.models import Q , Sum


# MAIN DOMAIN HOME (marketing / vendor signup links)
def home_view(request):
    # show list of vendors on the main site
    vendors = Vendor.objects.all()
    return render(request, "home.html", {"vendors": vendors})


def vendor_store(request, vendor_slug):
    # Get vendor by slug
    vendor = get_object_or_404(Vendor, slug=vendor_slug)

    # === CART COUNT (for navbar) ===
    cart_count = 0
    if 'cart_id' in request.session:
        try:
            cart = Cart.objects.get(id=request.session['cart_id'])
            cart_count = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
        except Cart.DoesNotExist:
            pass

    # === BASE QUERY: ONLY THIS VENDOR'S PRODUCTS ===
    products = Product.objects.filter(vendor=vendor)

    # === SEARCH ===
    q = request.GET.get('q')
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )

    # === CATEGORY FILTER ===
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    # === PRICE RANGE ===
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # === SORTING ===
    sort = request.GET.get('sort', '-created_at')
    sort_map = {
        'price_asc': 'price',
        'price_desc': '-price',
        'name_asc': 'name',
        'name_desc': '-name',
        'date_asc': 'created_at',
        'date_desc': '-created_at',
    }
    products = products.order_by(sort_map.get(sort, '-created_at'))

    # === PAGINATION ===
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    # === CATEGORIES FOR FILTER ===
    categories = Category.objects.filter(product__vendor=vendor).distinct()

    # === CONTEXT ===
    context = {
        'vendor': vendor,
        'page_obj': page_obj,
        'categories': categories,
        'cart_count': cart_count,
        'year': 2025,
    }

    # === AJAX REQUEST (for infinite scroll / filters) ===
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, 'vendors/partials/product_grid.html', context)

    # === FULL PAGE ===
    return render(request, 'vendors/vendor_store.html', context)
# -------- vendor auth on MAIN DOMAIN (signup/login/logout) --------
def vendor_signup(request):
    if request.method == "POST":
        username = request.POST.get("username").strip()
        email = request.POST.get("email").strip()
        password = request.POST.get("password").strip()
        store_name = request.POST.get("store_name").strip()

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username exists")
            return redirect("vendors:vendor_signup")

        user = User.objects.create_user(username=username, email=email, password=password)
        slug = store_name.lower().strip().replace(" ", "-")
        # ensure unique slug
        base = slug
        i = 1
        while Vendor.objects.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1

        Vendor.objects.create(user=user, store_name=store_name, slug=slug)
        messages.success(request, "Vendor account created. Please log in.")
        return redirect("vendors:vendor_login")

    return render(request, "vendors/register.html")

def vendor_login(request):
    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password").strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("vendors:vendor_dashboard")
        messages.error(request, "Invalid credentials")
        return redirect("vendors:vendor_login")
    return render(request, "vendors/login.html")



@never_cache
def vendor_logout(request):
    logout(request)
    response = redirect('vendors:vendor_login')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

# -------- DASHBOARD PAGES: only accessible to vendor owner on MAIN DOMAIN --------

@login_required
def vendor_dashboard(request):
    if not hasattr(request.user, 'vendor'):
        messages.error(request, "Access denied.")
        return redirect('vendors:vendor_signup')

    vendor = request.user.vendor

    # Auto-fix slug
    if not vendor.slug:
        slug = slugify(vendor.store_name)
        base = slug
        i = 1
        while Vendor.objects.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1
        vendor.slug = slug
        vendor.save()
        messages.success(request, f"Store live: /{slug}/")

    response = render(request, "vendors/dashboard.html", {"vendor": vendor})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required
def vendor_orders(request):
    vendor = getattr(request.user, "vendor", None)
    if not vendor:
        raise Http404("Access denied")
    orders = vendor.orders.all().order_by("-created_at")
    return render(request, "vendors/vendor_orders.html", {"vendor": vendor, "orders": orders})

@login_required
def vendor_profile(request):
    vendor = getattr(request.user, "vendor", None)
    if not vendor:
        raise Http404("Access denied")
    if request.method == "POST":
        vendor.store_name = request.POST.get("store_name", vendor.store_name)
        vendor.description = request.POST.get("description", vendor.description)
        vendor.save()
        messages.success(request, "Profile updated")
        return redirect("vendor_profile")
    return render(request, "vendors/vendor_profile.html", {"vendor": vendor})
    
# ---------- PRODUCT CRUD (using YOUR form) ----------
@login_required
def vendor_product_create(request):
    vendor = request.user.vendor
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = vendor
            product.save()
            messages.success(request, f"'{product.name}' added!")
            return redirect('vendors:vendor_products')
    else:
        form = ProductForm()
    return render(request, 'vendors/product_form.html', {
        'form': form,
        'title': 'Add New Product',
        'vendor': vendor
    })


@login_required
def vendor_product_update(request, pk):
    vendor = request.user.vendor
    product = get_object_or_404(Product, pk=pk, vendor=vendor)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{product.name}' updated!")
            return redirect('vendors:vendor_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'vendors/product_form.html', {
        'form': form,
        'title': 'Edit Product',
        'product': product,
        'vendor': vendor
    })


@login_required
def vendor_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user.vendor)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect('vendors:vendor_products')
    return render(request, 'vendors/product_delete.html', {'product': product})
    
@login_required
def vendor_products(request):
    vendor = request.user.vendor
    products = vendor.products.all()

    # Search
    q = request.GET.get('q')
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )

    # Category filter
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    # Pagination
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, "vendors/vendor_products.html", {
        "vendor": vendor,
        "products": page_obj,
        "categories": Category.objects.filter(product__vendor=vendor).distinct(),
    })
def process_checkout(request, vendor_slug):
    vendor = get_object_or_404(Vendor, slug=vendor_slug)
    if 'cart_id' not in request.session:
        return redirect('cart:view_cart', vendor_slug)

    cart = Cart.objects.get(id=request.session['cart_id'])

    if request.method == "POST":
        name = request.POST['name']
        phone = request.POST['phone']
        address = request.POST['address']
        note = request.POST.get('note', '')

      # Create Order
        order = Order.objects.create(
          vendor=vendor,
          customer_name=name,
          customer_phone=phone,
          customer_address=address,
          note=note,
          total_price=cart.total_price
      )
        for item in cart.items.all():
            OrderItem.objects.create(
              order=order,
              product=item.product,
              quantity=item.quantity,
              price=item.product.price
          )

      # WhatsApp Message
        items = "\n".join([
          f"• {i.product.name} × {i.quantity} = ₦{i.total_price}"
          for i in cart.items.all()
      ])
        msg = urllib.parse.quote(f"""
*New Order!*

*From:* {name}
*Phone:* {phone}
*Address:* {address}
*Note:* {note}

*Items:*
{items}

*Total:* ₦{cart.total_price}
      """.strip())

        wa_url = f"https://wa.me/{vendor.whatsapp}?text={msg}"

      # Clear cart
        cart.items.all().delete()
        messages.success(request, "Order sent! Check WhatsApp.")

        return redirect(wa_url)

    return redirect('vendors:checkout', vendor_slug)