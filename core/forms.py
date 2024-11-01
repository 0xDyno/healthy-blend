# forms.py

from django import forms
from django.contrib.auth import authenticate
from .models import User, Product, Ingredient, Order


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        user = authenticate(username=username, password=password)
        if not user or not user.is_active:
            raise forms.ValidationError("Invalid login credentials")
        return self.cleaned_data

    def get_user(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        return authenticate(username=username, password=password)
