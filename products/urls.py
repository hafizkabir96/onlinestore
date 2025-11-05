# products/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.products_index, name="products_index"),
    path("category/<int:pk>/", views.category_view, name="category_view"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
]