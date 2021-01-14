from django.forms import ModelForm, Textarea
from .models import Review
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, ButtonHolder, Submit

class ReviewForm(ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'user_name', 'comment']
        widgets = {
            'comment': Textarea(attrs={'cols': 35, 'rows': 10})
        } 


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget = forms.PasswordInput)
    