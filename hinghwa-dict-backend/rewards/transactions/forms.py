from django import forms
from .models.transaction import Transaction


class TransactionInfoForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ("action", "points", "reason", "id")
