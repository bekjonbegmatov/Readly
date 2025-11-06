from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
from django.contrib.auth.models import User


class SignupForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            classes = 'w-full rounded-md border border-gray-300 bg-gray-50 px-3 py-2 outline-none focus:border-brand focus:ring-4 focus:ring-brand/20'
            field.widget.attrs.update({'class': classes})


class AvatarForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["avatar"]
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'w-full rounded-md border border-gray-300 bg-white px-3 py-2 outline-none focus:border-brand focus:ring-4 focus:ring-brand/20'
            })
        }


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name"]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full rounded-md border border-gray-300 bg-gray-50 px-3 py-2 outline-none focus:border-brand focus:ring-4 focus:ring-brand/20'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full rounded-md border border-gray-300 bg-gray-50 px-3 py-2 outline-none focus:border-brand focus:ring-4 focus:ring-brand/20'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full rounded-md border border-gray-300 bg-gray-50 px-3 py-2 outline-none focus:border-brand focus:ring-4 focus:ring-brand/20'
            }),
        }