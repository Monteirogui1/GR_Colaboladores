from django.db import models


class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField()
    data_criacao = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.nome


class ClienteBaseModel(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)

    class Meta:
        abstract = True