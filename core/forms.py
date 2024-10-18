from django import forms
from django.contrib.auth import authenticate
from .models import User, Product, Ingredient, Order


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user or not user.is_active:
            raise forms.ValidationError("Invalid login credentials")
        return self.cleaned_data

    def get_user(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        return authenticate(username=username, password=password)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'product_type', 'is_official']
        labels = {
            'product_type': 'Type',
            'is_official': 'Official Product',
        }


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'description', 'min_order', 'max_order', 'available', 'price_per_gram']


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_status']


class CustomProductForm(forms.Form):
    base_product = forms.ModelChoiceField(queryset=Product.objects.all(), label="Base Product")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ingredients = Ingredient.objects.filter(available=True)

        for ingredient in self.ingredients:
            self.fields[f'ingredient_{ingredient.id}'] = forms.IntegerField(
                label=ingredient.name,
                required=False,
                min_value=ingredient.min_order,
                max_value=ingredient.max_order,
                widget=forms.NumberInput(attrs={'class': 'ingredient-input'})
            )

    def clean(self):
        cleaned_data = super().clean()
        base_product = cleaned_data.get('base_product')

        if not base_product:
            raise forms.ValidationError("You must select a base product.")

        total_weight = sum(
            cleaned_data.get(f'ingredient_{ingredient.id}', 0)
            for ingredient in self.ingredients
        )

        if total_weight == 0:
            raise forms.ValidationError("You must add at least one ingredient.")

        return cleaned_data


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError(
                "Password and Confirm Password do not match"
            )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['payment_type']
