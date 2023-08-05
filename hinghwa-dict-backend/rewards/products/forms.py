from django import forms

from .models.product import Product


class ProductInfoForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "points", "quantity", "picture", "details")
