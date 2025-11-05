from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product_name','unit_price_cents','quantity')
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','vendor','customer_name','customer_phone','total_cents','status','created_at')
    list_filter = ('status','created_at','vendor')
    inlines = [OrderItemInline]
