# config/urls.py
from django.contrib import admin
from django.urls import path, include
from vendors.views import home_view, vendor_store

urlpatterns = [
    path("admin/", admin.site.urls),

    # Vendor management — runs on main domain (lvh.me/vendor/...)
    path("", include("vendors.urls")),

    # Product & cart base paths — on main domain they behave as public pages,
    # on subdomains middleware attaches request.vendor and views will enforce.
    path("products/", include("products.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),

    # Root homepage for main domain
    path("", home_view, name="home"),
]