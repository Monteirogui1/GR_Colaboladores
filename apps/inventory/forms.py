from django import forms
from .models import Machine, MachineGroup, BlockedSite, Notification


class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = [
            'hostname', 'ip_address', 'mac_address', 'group',
            'manufacturer', 'model', 'serial_number',
            'cpu', 'ram_gb', 'disk_space_gb', 'disk_free_gb',
            'os_caption', 'os_architecture', 'os_build',
            'gpu_name', 'antivirus_name'
        ]
        widgets = {
            'hostname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da máquina'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 192.168.1.100'}),
            'mac_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: AA:BB:CC:DD:EE:FF'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fabricante'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Modelo'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de série'}),
            'cpu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Processador'}),
            'ram_gb': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'GB', 'step': '0.01'}),
            'disk_space_gb': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'GB', 'step': '0.01'}),
            'disk_free_gb': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'GB', 'step': '0.01'}),
            'os_caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sistema Operacional'}),
            'os_architecture': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 64-bit'}),
            'os_build': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Build do SO'}),
            'gpu_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Placa de vídeo'}),
            'antivirus_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Antivírus instalado'}),
        }


class MachineGroupForm(forms.ModelForm):
    class Meta:
        model = MachineGroup
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do grupo'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Descrição do grupo', 'rows': 3}),
        }


class BlockedSiteForm(forms.ModelForm):
    class Meta:
        model = BlockedSite
        fields = ['url', 'machine', 'group']
        widgets = {
            'url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: facebook.com'}),
            'machine': forms.Select(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        machine = cleaned_data.get('machine')
        group = cleaned_data.get('group')

        if not machine and not group:
            raise forms.ValidationError('Selecione uma máquina ou um grupo.')

        if machine and group:
            raise forms.ValidationError('Selecione apenas uma máquina OU um grupo, não ambos.')

        return cleaned_data


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'message', 'sent_to_all', 'machines', 'groups']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título da notificação'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Mensagem', 'rows': 4}),
            'sent_to_all': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'machines': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 5}),
            'groups': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 5}),
        }