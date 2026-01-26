from django import forms
from .models import Fornecedor


STATUS_CHOICE = ((True, 'Ativo'), (False, 'Inativo'),)

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'status', 'contato', 'email', 'descricao']  # Inclui todos os campos editáveis
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite o nome do fornecedor'}),
            'status': forms.Select(attrs={'class': 'form-control'}, choices=STATUS_CHOICE),
            'contato': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: (11) 99999-9999'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemplo@dominio.com'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descrição do fornecedor'}),
        }
        labels = {
            'nome': 'Nome',
            'status': 'Status',
            'contato': 'Contato',
            'email': 'E-mail',
            'descricao': 'Descrição',
        }