# cart/urls.py
from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('<slug:vendor_slug>/', views.view_cart, name='view_cart'),
    path('<slug:vendor_slug>/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('<slug:vendor_slug>/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('<slug:vendor_slug>/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('<slug:vendor_slug>/checkout/', views.checkout, name='checkout'),
    path('<slug:vendor_slug>/count/', views.cart_count_api, name='cart_count_api'),
]