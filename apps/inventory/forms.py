from django import forms
from .models import Machine


class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = '__all__'