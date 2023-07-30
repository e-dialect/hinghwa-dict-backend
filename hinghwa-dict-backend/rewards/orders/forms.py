from django import forms

from ..models import Orders


class OrdersInfoForm(forms.ModelForm):
    class Meta:
        model = Orders
        fields = ("address", "telephone", "comment","full_name")
