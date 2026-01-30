from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuditoriaListView,
    AuditoriaCreateView,
    AuditoriaDetailView,
    AuditoriaExecutarView,
    AuditoriaVerificarItemView,
    AuditoriaDesverificarItemView,
    AuditoriaFinalizarView,
    AuditoriaCancelarView,
    AuditoriaDeleteView,
    AuditoriaRelatorioView,
    AuditoriaViewSet,
    AuditoriaItemViewSet,
    AuditoriaHistoricoViewSet
)

app_name = 'auditoria'

router = DefaultRouter()
router.register(r'auditorias', AuditoriaViewSet, basename='auditoria')
router.register(r'itens', AuditoriaItemViewSet, basename='auditoria-item')
router.register(r'historico', AuditoriaHistoricoViewSet, basename='auditoria-historico')


urlpatterns = [
    # Listagem e CRUD
    path('auditoria/', AuditoriaListView.as_view(), name='auditoria_list'),
    path('auditoria/criar/', AuditoriaCreateView.as_view(), name='auditoria_create'),
    path('auditoria/<int:pk>/', AuditoriaDetailView.as_view(), name='auditoria_detail'),
    path('auditoria/<int:pk>/deletar/', AuditoriaDeleteView.as_view(), name='auditoria_delete'),

    # Execução da auditoria
    path('auditoria/<int:pk>/executar/', AuditoriaExecutarView.as_view(), name='auditoria_executar'),
    path('auditoria/<int:pk>/verificar/<int:item_id>/', AuditoriaVerificarItemView.as_view(), name='auditoria_verificar_item'),
    path('auditoria/<int:pk>/desverificar/<int:item_id>/', AuditoriaDesverificarItemView.as_view(),
         name='auditoria_desverificar_item'),

    # Finalização e cancelamento
    path('auditoria/<int:pk>/finalizar/', AuditoriaFinalizarView.as_view(), name='auditoria_finalizar'),
    path('auditoria/<int:pk>/cancelar/', AuditoriaCancelarView.as_view(), name='auditoria_cancelar'),

    # Relatório
    path('auditoria/<int:pk>/relatorio/', AuditoriaRelatorioView.as_view(), name='auditoria_relatorio'),
    path('auditoria/api/', include(router.urls)),
]