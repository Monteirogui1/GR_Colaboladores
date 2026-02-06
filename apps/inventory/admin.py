from django.contrib import admin, messages
from .models import Machine, MachineGroup, BlockedSite, Notification
from import_export.admin import ImportExportMixin

@admin.register(MachineGroup)
class MachineGroupAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display  = ('name', 'description')
    search_fields = ('name',)

@admin.register(Machine)
class MachineAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display    = ('hostname', 'loggedUser', 'tpm', 'ip_address', 'group', 'is_online', 'last_seen', 'ram_gb', 'disk_free_gb')
    list_filter     = ('group', 'is_online', 'last_seen')
    search_fields   = ('hostname', 'ip_address')
    readonly_fields = ('last_seen',)

@admin.register(BlockedSite)
class BlockedSiteAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display  = ('url', 'machine', 'group')
    list_filter   = ('group', 'machine')
    search_fields = ('url',)

