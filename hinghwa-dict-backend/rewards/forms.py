from django import forms

from .models import Rewards, Title


class RewardsInfoForm(forms.ModelForm):
    class Meta:
        model = Rewards
        fields = ("name", "point", "left", "picture")


class TitleInfoForm(forms.ModelForm):
    class Meta:
        model = Title
        fields = ("name", "point", "color", "owned")
