from django.contrib import admin
from .models import Marca


class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao',)
    search_fields = ('nome',)


admin.site.register(Marca, MarcaAdmin)