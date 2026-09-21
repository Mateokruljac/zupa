"""Django admin registracije za Župa i vjernici."""
from django.contrib import admin

from pastoral.admin_mixins import ProtectedReferenceAdminMixin
from zupa_vjernici.models import EcclesiasticalJurisdiction


@admin.register(EcclesiasticalJurisdiction)
class EcclesiasticalJurisdictionAdmin(
    ProtectedReferenceAdminMixin,
    admin.ModelAdmin,
):
    """Biskupija ili Križevačka eparhija — referentni katalog, ne dnevni unos."""

    list_display = (
        'official_name', 'jurisdiction_type', 'canonical_tradition',
        'parent_jurisdiction', 'is_active',
    )
    list_filter = ('jurisdiction_type', 'canonical_tradition', 'is_active')
    search_fields = ('official_name', 'code')
    autocomplete_fields = ('parent_jurisdiction',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    fields = (
        'id', 'official_name', 'code', 'jurisdiction_type',
        'canonical_tradition', 'parent_jurisdiction', 'is_active',
        'created_at', 'updated_at',
    )

    def save_model(self, request, jurisdiction, form, change):
        jurisdiction.full_clean()
        super().save_model(request, jurisdiction, form, change)
