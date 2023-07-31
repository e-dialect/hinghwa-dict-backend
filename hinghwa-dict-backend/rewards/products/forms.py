from django import forms

from .models.product import Product


class ProductsInfoForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "points", "quantity", "picture", "details")
