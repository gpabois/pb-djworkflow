from django.db  import models
from django     import forms
from .models    import Task
from .engine    import ENGINE

class ContextForm(forms.ModelForm):
    def clean(self, *args, **kwargs):
        self.instance = self.task
        return super().clean(*args, **kwargs)
        
        