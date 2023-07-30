from django import forms

from ..models import Products


class ProductsInfoForm(forms.ModelForm):
    class Meta:
        model = Products
        fields = ("name", "points", "quantity", "picture", "details")
