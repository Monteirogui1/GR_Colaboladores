from django.urls import path
from .views import ClienteWizardView

urlpatterns = [
    path('novo-cliente/', ClienteWizardView.as_view(), name='cliente_wizard'),
]
