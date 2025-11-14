from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    name = forms.CharField(max_length=255, required=True)

    class Meta:
        model = User
        fields = ['username', 'name', 'password1', 'password2']