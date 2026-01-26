from django.urls import path, include
from django.contrib.auth.views import LoginView

from .views import ErpLoginView, ClienteUserListView, ClienteUserCreateView, ClienteUserUpdateView, \
    ClienteUserDeleteView

app_name = 'authentication'

urlpatterns = [
    path('', ErpLoginView.as_view(), name='login'),
    path('', include('django.contrib.auth.urls')),

    path('usuarios/', ClienteUserListView.as_view(), name='clienteuser_list'),
    path('usuarios/novo/', ClienteUserCreateView.as_view(), name='clienteuser_create'),
    path('usuarios/<int:pk>/editar/', ClienteUserUpdateView.as_view(), name='clienteuser_update'),
    path('usuarios/<int:pk>/excluir/', ClienteUserDeleteView.as_view(), name='clienteuser_delete'),
]