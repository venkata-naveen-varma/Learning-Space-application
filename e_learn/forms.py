from django import forms
from .models import User
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(AuthenticationForm):
    """ Login form to allow user to enter credentials """
    class Meta:
        model = User
        fields = ('username', 'password')
