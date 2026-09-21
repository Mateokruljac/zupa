from django.contrib import admin

from core.models import Settings
from pastoral.admin_mixins import ParishTechnicalAdminMixin


@admin.register(Settings)
class SettingsAdmin(ParishTechnicalAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'unified_key', 'created_at', 'updated_at')
    fields = (
        'name',
        'value',
        'description',
        'is_active',
        'id',
        'unified_key',
        'created_at',
        'updated_at',
    )
