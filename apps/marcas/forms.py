from django import forms
from .models import Marca


STATUS_CHOICE = ((True, 'Ativo'), (False, 'Inativo'),)

class MarcaForm(forms.ModelForm):

    class Meta:
        model = Marca
        fields = ['nome', 'status', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}, choices=STATUS_CHOICE),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'nome': 'Nome',
            'status': 'Status',
            'descricao': 'Descrição',
        }