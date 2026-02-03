from django.db import models
from apps.shared.models import ClienteBaseModel
from apps.ativos.models import Localizacao, Ativo
from apps.authentication.models import User


class Auditoria(ClienteBaseModel, models.Model):
    STATUS_CHOICES = [
        ('0', 'Em Andamento'),
        ('1', 'Finalizada'),
        ('2', 'Cancelada'),
    ]

    titulo = models.CharField("Título", max_length=200)
    localizacao = models.ForeignKey(
        Localizacao,
        on_delete=models.CASCADE,
        verbose_name="Localização/Filial"
    )
    responsavel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='auditorias_responsavel',
        verbose_name="Responsável"
    )
    status = models.CharField(
        "Status",
        max_length=1,
        choices=STATUS_CHOICES,
        default='0'
    )
    data_inicio = models.DateTimeField("Data de Início", auto_now_add=True)
    data_finalizacao = models.DateTimeField("Data de Finalização", null=True, blank=True)
    observacoes = models.TextField("Observações", blank=True, null=True)

    # Estatísticas
    total_ativos = models.IntegerField("Total de Ativos", default=0)
    ativos_verificados = models.IntegerField("Ativos Verificados", default=0)
    ativos_nao_encontrados = models.IntegerField("Ativos Não Encontrados", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_inicio']
        verbose_name = "Auditoria"
        verbose_name_plural = "Auditorias"

    def __str__(self):
        return f"{self.titulo} - {self.localizacao.nome} ({self.get_status_display()})"

    def calcular_progresso(self):
        """Calcula o percentual de progresso da auditoria"""
        if self.total_ativos == 0:
            return 0
        return round((self.ativos_verificados / self.total_ativos) * 100, 2)

    def atualizar_estatisticas(self):
        """Atualiza as estatísticas da auditoria"""
        itens = self.itens.all()
        self.ativos_verificados = itens.filter(verificado=True).count()
        self.ativos_nao_encontrados = itens.filter(
            verificado=False,
            observacao__icontains='não encontrado'
        ).count()
        self.save()


class AuditoriaItem(models.Model):
    auditoria = models.ForeignKey(
        Auditoria,
        on_delete=models.CASCADE,
        related_name='itens'
    )
    ativo = models.ForeignKey(
        Ativo,
        on_delete=models.CASCADE,
        verbose_name="Ativo"
    )
    verificado = models.BooleanField("Verificado", default=False)
    data_verificacao = models.DateTimeField("Data de Verificação", null=True, blank=True)
    verificado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Verificado Por"
    )
    observacao = models.TextField("Observação", blank=True, null=True)

    # Campos para registro de alterações durante a auditoria
    estado_fisico = models.CharField(
        "Estado Físico",
        max_length=1,
        blank=True,
        null=True,
        choices=[
            ('0', 'Ótimo'),
            ('1', 'Bom'),
            ('2', 'Regular'),
            ('3', 'Ruim'),
        ]
    )
    localizacao_real = models.CharField(
        "Localização Real (se diferente)",
        max_length=200,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ativo__etiqueta']
        verbose_name = "Item da Auditoria"
        verbose_name_plural = "Itens da Auditoria"
        unique_together = ['auditoria', 'ativo']

    def __str__(self):
        status = "✓" if self.verificado else "✗"
        return f"{status} {self.ativo.etiqueta} - {self.ativo.nome}"


class AuditoriaHistorico(models.Model):
    auditoria = models.ForeignKey(
        Auditoria,
        on_delete=models.CASCADE,
        related_name='historico'
    )
    acao = models.CharField("Ação", max_length=100)
    descricao = models.TextField("Descrição")
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Usuário"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Histórico da Auditoria"
        verbose_name_plural = "Históricos das Auditorias"

    def __str__(self):
        return f"{self.auditoria.titulo} - {self.acao} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"