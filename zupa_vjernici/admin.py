"""Django admin registracije za Župa i vjernici."""
from django.contrib import admin

from pastoral.admin_mixins import ProtectedReferenceAdminMixin
from zupa_vjernici.models import ChurchSuiIuris, EcclesiasticalJurisdiction


@admin.register(ChurchSuiIuris)
class ChurchSuiIurisAdmin(ProtectedReferenceAdminMixin, admin.ModelAdmin):
    list_display = (
        'official_name', 'code', 'canonical_tradition',
        'default_liturgical_tradition', 'is_active',
    )
    list_filter = ('canonical_tradition', 'is_active')
    search_fields = ('official_name', 'short_name', 'code')
    autocomplete_fields = ('default_liturgical_tradition',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    fields = (
        'id', 'official_name', 'short_name', 'code', 'canonical_tradition',
        'default_liturgical_tradition', 'is_active', 'created_at', 'updated_at',
    )


@admin.register(EcclesiasticalJurisdiction)
class EcclesiasticalJurisdictionAdmin(
    ProtectedReferenceAdminMixin,
    admin.ModelAdmin,
):
    list_display = (
        'official_name', 'jurisdiction_type', 'church_sui_iuris',
        'parent_jurisdiction', 'is_active',
    )
    list_filter = ('jurisdiction_type', 'church_sui_iuris', 'is_active')
    search_fields = ('official_name', 'code')
    autocomplete_fields = ('church_sui_iuris', 'parent_jurisdiction')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fields = (
        'id', 'official_name', 'code', 'jurisdiction_type',
        'church_sui_iuris', 'parent_jurisdiction', 'is_active',
        'created_at', 'updated_at',
    )

    def save_model(self, request, jurisdiction, form, change):
        jurisdiction.full_clean()
        super().save_model(request, jurisdiction, form, change)
