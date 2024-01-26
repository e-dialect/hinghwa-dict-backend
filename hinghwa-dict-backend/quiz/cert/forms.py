from django import forms
from ..models import Cert


class CertForm(forms.ModelForm):
    class Meta:
        model = Cert
        fields = ("level", "name", "place", "sequence", "grade", "scores")
