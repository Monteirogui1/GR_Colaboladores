from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class UserAdmin(BaseUserAdmin):
    # Campos a serem exibidos na listagem de usuários no admin
    list_display = ('username', 'email', 'first_name', 'last_name', 'cliente', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'cliente')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    # Campos editáveis diretamente na lista
    list_editable = ('is_staff', 'is_active')

    # Para garantir que 'cliente' apareça no cadastro/edição
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações pessoais', {'fields': ('first_name', 'last_name', 'email', 'cliente')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'cliente', 'password1', 'password2', 'is_staff', 'is_active', 'is_superuser'),
        }),
    )

admin.site.register(User, UserAdmin)
