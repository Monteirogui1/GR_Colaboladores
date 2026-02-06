from django import forms
from .models import Machine, MachineGroup, BlockedSite, Notification, AgentVersion


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
    '''Form para criar/editar notificações'''

    class Meta:
        model = Notification
        fields = [
            'machine',
            'title',
            'message',
            'type',
            'priority',
            'expires_at',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o título da notificação'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Digite a mensagem completa'
            }),
            'type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'machine': forms.Select(attrs={
                'class': 'form-control'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }


class BulkNotificationForm(forms.Form):
    '''Form para criar notificações em massa'''

    machines = forms.ModelMultipleChoiceField(
        queryset=Machine.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Máquinas',
        help_text='Selecione as máquinas que receberão a notificação'
    )

    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Título da notificação'
        })
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Mensagem completa'
        })
    )

    type = forms.ChoiceField(
        choices=Notification.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='info'
    )

    priority = forms.ChoiceField(
        choices=Notification.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='normal'
    )

    expires_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label='Expira em (opcional)'
    )


class AgentTokenGenerateForm(forms.Form):
    """Formulário para geração de tokens"""

    quantity = forms.IntegerField(
        label="Quantidade de Tokens",
        min_value=1,
        max_value=50,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ex: 1'
        }),
        help_text="Gere até 50 tokens de uma vez"
    )

    days = forms.ChoiceField(
        label="Validade (dias)",
        choices=[
            (1, '1 dia'),
            (3, '3 dias'),
            (7, '7 dias (recomendado)'),
            (14, '14 dias'),
            (30, '30 dias'),
            (60, '60 dias'),
            (90, '90 dias'),
            (180, '180 dias'),
            (365, '365 dias (1 ano)'),
        ],
        initial=7,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg'
        }),
        help_text="Tempo até o token expirar"
    )


class AgentVersionForm(forms.ModelForm):
    """Formulário para criação de versão do agente"""

    class Meta:
        model = AgentVersion
        fields = ['version', 'file_path', 'release_notes', 'is_mandatory']
        widgets = {
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 2.1.0'
            }),
            'file_path': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.py'
            }),
            'release_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': '- Correções de bugs\n- Melhorias de performance\n- Novas funcionalidades'
            }),
            'is_mandatory': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'version': 'Versão',
            'file_path': 'Arquivo do Agente (agent.py)',
            'release_notes': 'Notas de Lançamento',
            'is_mandatory': 'Atualização Obrigatória',
        }
        help_texts = {
            'version': 'Formato: MAJOR.MINOR.PATCH (ex: 2.1.0)',
            'file_path': 'Arquivo Python do agente atualizado',
            'release_notes': 'Descreva as mudanças nesta versão',
            'is_mandatory': 'Se marcado, todos os agentes serão forçados a atualizar',
        }

    def clean_version(self):
        """Valida formato da versão"""
        version = self.cleaned_data.get('version')

        # Verifica formato básico
        if not version:
            raise forms.ValidationError("Versão é obrigatória")

        # Valida formato (simplificado)
        parts = version.split('.')
        if len(parts) != 3:
            raise forms.ValidationError(
                "Versão deve estar no formato MAJOR.MINOR.PATCH (ex: 2.1.0)"
            )

        try:
            for part in parts:
                int(part)
        except ValueError:
            raise forms.ValidationError(
                "Versão deve conter apenas números separados por pontos"
            )

        return version

    def clean_file_path(self):
        """Valida arquivo do agente"""
        file = self.cleaned_data.get('file_path')

        if file:
            # Verifica extensão
            if not file.name.endswith('.py'):
                raise forms.ValidationError(
                    "Arquivo deve ser um script Python (.py)"
                )

            # Verifica tamanho (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    "Arquivo muito grande. Tamanho máximo: 5MB"
                )

        return file