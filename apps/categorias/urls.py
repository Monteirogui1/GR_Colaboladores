from django.urls import path

from .views import CategoriaListView, CategoriaCreateView, CategoriaDetailView, CategoriaUpdateView, \
    CategoriaDeleteView

app_name = 'categorias'

urlpatterns = [
    path('Categoria/', CategoriaListView.as_view(), name='categoria_list'),
    path('Categoria/criar/', CategoriaCreateView.as_view(), name='categoria_form'),
    path('Categoria/<int:pk>/detalhe/', CategoriaDetailView.as_view(), name='categoria_detail'),
    path('Categoria/<int:pk>/atualizar/', CategoriaUpdateView.as_view(), name='categoria_form'),
    path('Categoria/<int:pk>/deletar/', CategoriaDeleteView.as_view(), name='categoria_delete'),
]