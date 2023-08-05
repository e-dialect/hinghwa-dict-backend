from django import forms

from .models import User, UserInfo


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = (
            "nickname",
            "birthday",
            "telephone",
            "avatar",
            "county",
            "town",
        )


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "password", "email")

    def clean_email(self):
        cd = self.cleaned_data
        if str(cd["email"]).find("@") == -1:
            raise forms.ValidationError("Invalid Email")
        return cd["email"]


class UserFormByWechat(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "password")
