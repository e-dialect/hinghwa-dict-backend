from django import forms
from ..models import Transactions


class TransactionsInfoForm(forms.ModelForm):
    class Meta:
        model = Transactions
        fields = ("action", "points", "reason", "id")
