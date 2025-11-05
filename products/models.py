from django.db import models
from vendors.models import Vendor

# products/models.py
class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    @property
    def get_indented_name(self):
        level = 0
        p = self.parent
        while p:
            level += 1
            p = p.parent
        return "└" + "─" * level + " " + self.name

    def get_depth(self):
        level = 0
        p = self.parent
        while p:
            level += 1
            p = p.parent
        return level
    


class Product(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image_url = models.URLField(blank=True, null=True)
    order_via_whatsapp = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def whatsapp_order_link(self):
        if self.order_via_whatsapp and self.vendor.whatsapp_number:
            msg = f"Hello! I'm interested in {self.name}."
            return f"https://wa.me/{self.vendor.whatsapp_number}?text={msg}"
        return None
