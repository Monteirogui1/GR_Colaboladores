from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.shared.models import Cliente

class User(AbstractUser):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True)
