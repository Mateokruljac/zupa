from django.contrib import admin

from .models import ParishWebsite, ParishWebsiteMedia, PublicContentPublication, WebsiteBuild


class WebsiteBuildInline(admin.TabularInline):
    model = WebsiteBuild
    extra = 0
    can_delete = False
    readonly_fields = (
        'id', 'kind', 'status', 'progress', 'requested_by', 'metadata',
        'queued_at', 'started_at', 'finished_at',
    )

    def has_add_permission(self, request, obj=None):
        return False


class ParishWebsiteMediaInline(admin.TabularInline):
    model = ParishWebsiteMedia
    extra = 0
    fields = ('kind', 'image', 'alt_text', 'caption', 'sort_order', 'is_visible', 'created_by')
    readonly_fields = ('created_by',)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ParishWebsite)
class ParishWebsiteAdmin(admin.ModelAdmin):
    list_display = ('parish', 'status', 'publication_status', 'template_key', 'subdomain', 'custom_domain', 'updated_at')
    list_filter = ('status', 'publication_status', 'template_key')
    search_fields = ('parish__slug', 'site_name', 'subdomain', 'custom_domain')
    autocomplete_fields = ('parish', 'requested_by')
    readonly_fields = ('id', 'activated_at', 'published_at', 'created_at', 'updated_at')
    inlines = (ParishWebsiteMediaInline, WebsiteBuildInline)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WebsiteBuild)
class WebsiteBuildAdmin(admin.ModelAdmin):
    list_display = ('website', 'kind', 'status', 'progress', 'queued_at', 'finished_at')
    list_filter = ('kind', 'status')
    search_fields = ('website__parish__slug', 'website__site_name')
    readonly_fields = (
        'id', 'website', 'kind', 'status', 'progress', 'requested_by',
        'metadata', 'queued_at', 'started_at', 'finished_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return bool(obj is None and super().has_change_permission(request, obj))

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ParishWebsiteMedia)
class ParishWebsiteMediaAdmin(admin.ModelAdmin):
    list_display = ('website', 'kind', 'caption', 'width', 'height', 'file_size', 'is_visible', 'created_at')
    list_filter = ('kind', 'is_visible')
    search_fields = ('website__site_name', 'website__parish__slug', 'alt_text', 'caption')
    autocomplete_fields = ('website', 'created_by')
    readonly_fields = ('id', 'width', 'height', 'file_size', 'created_at')


@admin.register(PublicContentPublication)
class PublicContentPublicationAdmin(admin.ModelAdmin):
    list_display = ('website', 'kind', 'source_label', 'status', 'scheduled_for', 'updated_at')
    list_filter = ('kind', 'status')
    search_fields = ('website__site_name', 'website__parish__slug', 'source_label')
    autocomplete_fields = ('website', 'updated_by')
    readonly_fields = ('id', 'source_key', 'created_at', 'updated_at')
