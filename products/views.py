# products/views.py
from django.shortcuts import render, get_object_or_404
from .models import Product, Category

def products_index(request):
    # if on a vendor subdomain, show only that vendor's products
    vendor = getattr(request, "vendor", None)
    if vendor:
        qs = Product.objects.filter(vendor=vendor, is_active=True)
    else:
        qs = Product.objects.filter(is_active=True)
    return render(request, "products/index.html", {"products": qs, "vendor": vendor})

def category_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    vendor = getattr(request, "vendor", None)
    if vendor:
        products = category.product_set.filter(vendor=vendor, is_active=True)
    else:
        products = category.product_set.filter(is_active=True)
    return render(request, "products/category.html", {"category": category, "products": products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # ensure product belongs to request.vendor when on subdomain
    vendor = getattr(request, "vendor", None)
    if vendor and product.vendor != vendor:
        raise Http404("Product not found on this store")
    return render(request, "products/detail.html", {"product": product, "vendor": vendor})