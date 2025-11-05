# products/forms.py
from django import forms
from products.models import Product, Category


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'price',
            'stock', 'image_url', 'order_via_whatsapp', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show indented categories
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "— Select Category —"