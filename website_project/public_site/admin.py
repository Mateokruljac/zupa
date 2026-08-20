from django.contrib import admin

from .models import ParishWebsite, ParishWebsiteMedia


class ParishWebsiteMediaInline(admin.TabularInline):
    model = ParishWebsiteMedia
    extra = 0
    fields = (
        'kind',
        'image',
        'alt_text',
        'caption',
        'sort_order',
        'is_visible',
        'created_by',
    )
    readonly_fields = ('created_by',)


@admin.register(ParishWebsite)
class ParishWebsiteAdmin(admin.ModelAdmin):
    list_display = (
        'site_name',
        'parish_identifier',
        'status',
        'template_key',
        'subdomain',
        'custom_domain',
        'updated_at',
    )
    list_filter = ('status', 'template_key')
    search_fields = (
        'parish_identifier',
        'site_name',
        'subdomain',
        'custom_domain',
    )
    readonly_fields = ('id', 'activated_at', 'published_at', 'created_at', 'updated_at')
    inlines = (ParishWebsiteMediaInline,)


@admin.register(ParishWebsiteMedia)
class ParishWebsiteMediaAdmin(admin.ModelAdmin):
    list_display = (
        'website',
        'kind',
        'caption',
        'width',
        'height',
        'file_size',
        'is_visible',
        'created_at',
    )
    list_filter = ('kind', 'is_visible')
    search_fields = ('website__site_name', 'alt_text', 'caption')
    autocomplete_fields = ('website', 'created_by')
    readonly_fields = ('id', 'width', 'height', 'file_size', 'created_at')
