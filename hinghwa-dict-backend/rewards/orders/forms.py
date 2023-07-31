from django import forms

from .models.order import Order


class OrdersInfoForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("address", "telephone", "comment", "full_name")
