from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

from .models import (
    Category, EmployeeProfile, Medicine, Supplier, Supply, SupplyItem, UserRole,
)


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'}),
    )


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = [
            'name', 'category', 'manufacturer', 'price', 'quantity',
            'expiry_date', 'barcode', 'description', 'received_date',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'received_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'phone', 'address', 'email', 'debt']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'debt': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class SupplyForm(forms.ModelForm):
    class Meta:
        model = Supply
        fields = ['supplier', 'paid_amount', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class SupplyItemForm(forms.ModelForm):
    class Meta:
        model = SupplyItem
        fields = ['medicine', 'quantity', 'unit_price']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


SupplyItemFormSet = forms.inlineformset_factory(
    Supply, SupplyItem, form=SupplyItemForm, extra=3, can_delete=True
)


class EmployeeForm(forms.ModelForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        label='Пароль', required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Оставьте пустым, чтобы не менять пароль',
    )

    class Meta:
        model = EmployeeProfile
        fields = ['fullname', 'position', 'role', 'phone']
        widgets = {
            'fullname': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)
        if self.user_instance:
            self.fields['username'].initial = self.user_instance.username

    def save(self, commit=True):
        profile = super().save(commit=False)
        username = self.cleaned_data['username']
        password = self.cleaned_data.get('password')
        if self.user_instance:
            user = self.user_instance
            user.username = username
            if password:
                user.set_password(password)
            user.save()
        else:
            user = User.objects.create_user(username=username, password=password or 'password123')
        profile.user = user
        if commit:
            profile.save()
        return profile


class SaleCartItemForm(forms.Form):
    medicine_id = forms.IntegerField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
