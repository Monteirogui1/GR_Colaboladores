from django.contrib import admin
from .models import Fornecedor


class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao',)
    search_fields = ('nome',)


admin.site.register(Fornecedor, FornecedorAdmin)