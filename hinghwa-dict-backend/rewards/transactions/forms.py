from django import forms
from .models.transaction import Transaction


class TransactionsInfoForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ("action", "points", "reason", "id")
