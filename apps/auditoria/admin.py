from django.contrib import admin
from .models import Auditoria, AuditoriaItem, AuditoriaHistorico


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'localizacao', 'responsavel', 'status', 'progresso_display', 'data_inicio')
    list_filter = ('status', 'localizacao', 'data_inicio')
    search_fields = ('titulo', 'localizacao__nome')
    date_hierarchy = 'data_inicio'
    readonly_fields = ('total_ativos', 'ativos_verificados', 'ativos_nao_encontrados', 'created_at', 'updated_at')

    def progresso_display(self, obj):
        return f"{obj.calcular_progresso()}%"
    progresso_display.short_description = 'Progresso'


@admin.register(AuditoriaItem)
class AuditoriaItemAdmin(admin.ModelAdmin):
    list_display = ('ativo', 'auditoria', 'verificado', 'estado_fisico', 'data_verificacao', 'verificado_por')
    list_filter = ('verificado', 'estado_fisico', 'auditoria')
    search_fields = ('ativo__etiqueta', 'ativo__nome', 'auditoria__titulo')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AuditoriaHistorico)
class AuditoriaHistoricoAdmin(admin.ModelAdmin):
    list_display = ('auditoria', 'acao', 'usuario', 'created_at')
    list_filter = ('acao', 'created_at')
    search_fields = ('auditoria__titulo', 'descricao')
    readonly_fields = ('created_at',)