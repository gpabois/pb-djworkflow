from django import forms
from pb_djworkflow.forms import ContextForm
from . import models

class CreateForm(forms.ModelForm):
    class Meta:
        model = models.SimpleContext
        fields = []

class SimpleForm(forms.ModelForm):
    class Meta:
        model = models.SimpleContext
        fields = ['approval_decision']
