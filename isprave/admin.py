"""Django admin registracije za Isprave."""
from django.contrib import admin

from isprave.models import RegisterTemplate, RegisterTemplateVersion
from pastoral.admin_mixins import ProtectedReferenceAdminMixin


@admin.register(RegisterTemplate)
class RegisterTemplateAdmin(ProtectedReferenceAdminMixin, admin.ModelAdmin):
    list_display = (
        'name', 'event_type', 'owner_scope', 'canonical_tradition',
        'is_official', 'is_active',
    )
    list_filter = (
        'event_type', 'owner_scope', 'canonical_tradition',
        'is_official', 'is_active',
    )
    search_fields = ('name', 'code')
    autocomplete_fields = ('ecclesiastical_jurisdiction',)
    readonly_fields = ('id',)

    def save_model(self, request, register_template, form, change):
        register_template.full_clean()
        super().save_model(request, register_template, form, change)


@admin.register(RegisterTemplateVersion)
class RegisterTemplateVersionAdmin(ProtectedReferenceAdminMixin, admin.ModelAdmin):
    list_display = ('template', 'version_number', 'status', 'effective_from', 'published_at')
    list_filter = ('status', 'template__event_type')
    search_fields = ('template__name', 'template__code')
    autocomplete_fields = ('template', 'published_by')
    readonly_fields = ('id', 'created_at', 'updated_at')
