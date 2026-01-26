from django import forms
from .models import Cliente

class ImportForm(forms.Form):
    file_format = forms.ChoiceField(
        choices=(
            ('CSV', 'CSV'),
            ('JSON', 'JSON'),
            ('XLSX', 'XLSX'),
        ),
        label='Formato do Arquivo',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    import_file = forms.FileField(
        label='Arquivo para Importação',
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

class ClienteWizardForm(forms.ModelForm):
    senha_admin = forms.CharField(
        label='Senha do admin', widget=forms.PasswordInput, required=False,
        help_text='(Opcional) Cria usuário admin inicial'
    )
    email_admin = forms.EmailField(label='E-mail do admin', required=False)

    class Meta:
        model = Cliente
        fields = ['nome', 'email', 'cnpj']