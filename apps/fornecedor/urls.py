from django.urls import path

from .views import FornecedorListView, FornecedorCreateView, FornecedorDetailView, FornecedorUpdateView, \
    FornecedorDeleteView

app_name = 'fornecedores'

urlpatterns = [
    path('Fornecedor/', FornecedorListView.as_view(), name='fornecedores_list'),
    path('Fornecedor/criar/', FornecedorCreateView.as_view(), name='fornecedores_form'),
    path('Fornecedor/<int:pk>/detalhe/', FornecedorDetailView.as_view(), name='fornecedor_detail'),
    path('Fornecedor/<int:pk>/atualizar/', FornecedorUpdateView.as_view(), name='fornecedores_form'),
    path('Fornecedor/<int:pk>/deletar/', FornecedorDeleteView.as_view(), name='fornecedor_delete'),
]