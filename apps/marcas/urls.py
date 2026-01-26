from django.urls import path

from .views import MarcaCreateView, MarcaListView, MarcaDetailView, MarcaDeleteView, MarcaUpdateView


app_name = 'marcas'

urlpatterns = [
    path('Marca/', MarcaListView.as_view(), name='marca_list'),
    path('Marca/criar/', MarcaCreateView.as_view(), name='marca_form'),
    path('Marca/<int:pk>/detale/', MarcaDetailView.as_view(), name='marca_detail'),
    path('Marca/<int:pk>/atualizar/', MarcaUpdateView.as_view(), name='marca_form'),
    path('Marca/<int:pk>/deletar/', MarcaDeleteView.as_view(), name='marca_delete'),
]