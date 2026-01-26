from django import forms
from .models import Categoria

STATUS_CHOICE = ((True, 'Ativo'), (False, 'Inativo'),)

class CategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria
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