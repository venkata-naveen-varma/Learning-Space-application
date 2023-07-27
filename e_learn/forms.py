from django import forms
from .models import User
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    """ Login form to allow user to enter credentials """
    username = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'placeholder': 'Enter your username'}))
    password = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}))

    class Meta:
        model = User
        fields = ('username', 'password')
