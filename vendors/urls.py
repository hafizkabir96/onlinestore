# vendors/urls.py
from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    # Main domain pages
    path('', views.home_view, name='home'),                    # lvh.me:8000/
    path('signup/', views.vendor_signup, name='vendor_signup'),
    path('login/', views.vendor_login, name='vendor_login'),
    path('logout/', views.vendor_logout, name='vendor_logout'),

    # Vendor dashboard (main domain)
    path('dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('dashboard/products/', views.vendor_products, name='vendor_products'),
    path('dashboard/orders/', views.vendor_orders, name='vendor_orders'),
    path('dashboard/profile/', views.vendor_profile, name='vendor_profile'),

    # Subdomain store
    path('<slug:vendor_slug>/', views.vendor_store, name='vendor_store'),
    path('products/add/', views.vendor_product_create, name='vendor_product_create'),
    path('products/<int:pk>/edit/', views.vendor_product_update, name='vendor_product_update'),
    path('products/<int:pk>/delete/', views.vendor_product_delete, name='vendor_product_delete'),
    # vendors/urls.py
    path('<slug:vendor_slug>/checkout/process/', views.process_checkout, name='process_checkout'),
]