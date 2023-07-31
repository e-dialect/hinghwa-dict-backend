from django import forms
from .models.title import Title


class TitleInfoForm(forms.ModelForm):
    class Meta:
        model = Title
        fields = ("name", "points", "color")
