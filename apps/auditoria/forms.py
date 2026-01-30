from django import forms
from .models import Auditoria, AuditoriaItem


class AuditoriaForm(forms.ModelForm):
    class Meta:
        model = Auditoria
        fields = ['titulo', 'localizacao', 'responsavel', 'observacoes']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Auditoria Anual 2026'
            }),
            'localizacao': forms.Select(attrs={'class': 'form-control'}),
            'responsavel': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações gerais sobre a auditoria'
            }),
        }
        labels = {
            'titulo': 'Título da Auditoria',
            'localizacao': 'Localização/Filial',
            'responsavel': 'Responsável',
            'observacoes': 'Observações',
        }


class AuditoriaItemForm(forms.ModelForm):
    class Meta:
        model = AuditoriaItem
        fields = ['estado_fisico', 'localizacao_real', 'observacao']
        widgets = {
            'estado_fisico': forms.Select(attrs={'class': 'form-control'}),
            'localizacao_real': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Informe se o ativo está em local diferente'
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observações sobre o ativo'
            }),
        }
        labels = {
            'estado_fisico': 'Estado Físico',
            'localizacao_real': 'Localização Real',
            'observacao': 'Observação',
        }


class FinalizarAuditoriaForm(forms.Form):
    observacoes_finais = forms.CharField(
        label='Observações Finais',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Adicione observações finais sobre a auditoria'
        }),
        required=False
    )

    confirmar = forms.BooleanField(
        label='Confirmo que desejo finalizar esta auditoria',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )