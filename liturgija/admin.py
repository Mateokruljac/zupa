"""Django admin registracije za Liturgija."""
import json

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from liturgija.models import (
    LiturgicalCalendarEntry,
    LiturgicalCalendarImport,
    LiturgicalTradition,
)
from liturgija.services.liturgical_imports import (
    clear_imported_calendar_cache,
    extract_calendar_events,
    prepare_calendar_import,
    replace_calendar_entries,
)
from pastoral.admin_mixins import (
    ParishTechnicalAdminMixin,
    ProtectedReferenceAdminMixin,
)


@admin.register(LiturgicalTradition)
class LiturgicalTraditionAdmin(ProtectedReferenceAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fields = ('id', 'name', 'code', 'is_active', 'created_at', 'updated_at')


class LiturgicalCalendarImportAdminForm(forms.ModelForm):
    calendar_file = forms.FileField(
        label='LitCal JSON datoteka',
        required=False,
        help_text=(
            'Prihvaća LitCal JSON s popisom događaja u ključu „litcal” ili '
            '„Litcal”. Ponovni upload zamjenjuje prethodni sadržaj te godine.'
        ),
    )

    class Meta:
        model = LiturgicalCalendarImport
        fields = ('year', 'provider', 'calendar_file')

    def clean(self):
        cleaned_data = super().clean()
        uploaded_calendar_file = cleaned_data.get('calendar_file')
        if not uploaded_calendar_file:
            if not self.instance.pk:
                self.add_error('calendar_file', 'Odaberite kalendarsku JSON datoteku.')
            return cleaned_data

        maximum_calendar_file_size = 10 * 1024 * 1024
        if uploaded_calendar_file.size > maximum_calendar_file_size:
            self.add_error(
                'calendar_file',
                'Kalendarska datoteka ne smije biti veća od 10 MB.',
            )
            return cleaned_data

        try:
            payload = json.loads(uploaded_calendar_file.read().decode('utf-8-sig'))
        except (UnicodeDecodeError, json.JSONDecodeError) as validation_error:
            self.add_error(
                'calendar_file',
                f'Datoteka nije valjan UTF-8 JSON: {validation_error}',
            )
            return cleaned_data

        calendar_year = cleaned_data.get('year')
        if calendar_year:
            try:
                self.validated_calendar_events = extract_calendar_events(
                    payload,
                    calendar_year,
                )
            except ValidationError as validation_error:
                self.add_error('calendar_file', validation_error)
        return cleaned_data


@admin.register(LiturgicalCalendarImport)
class LiturgicalCalendarImportAdmin(ParishTechnicalAdminMixin, admin.ModelAdmin):
    form = LiturgicalCalendarImportAdminForm
    list_display = (
        'year', 'provider', 'event_count', 'source_file_name',
        'imported_by', 'imported_at',
    )
    list_filter = ('provider', 'year')
    search_fields = ('=year', 'source_file_name', 'checksum')
    date_hierarchy = 'imported_at'
    fields = (
        'year', 'provider', 'calendar_file', 'event_count',
        'source_file_name', 'checksum', 'imported_by', 'imported_at',
        'events_preview', 'created_at', 'updated_at',
    )
    readonly_fields = (
        'event_count', 'source_file_name', 'checksum', 'imported_by',
        'imported_at', 'events_preview', 'created_at', 'updated_at',
    )

    @admin.display(description='Uvezeni događaji — samo pregled')
    def events_preview(self, calendar_import):
        if not calendar_import.pk:
            return 'Događaji će biti prikazani nakon uspješnog uvoza.'
        preview_events = (calendar_import.events or [])[:20]
        rendered_events = json.dumps(
            preview_events,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        remaining_event_count = max(
            calendar_import.event_count - len(preview_events),
            0,
        )
        suffix = (
            f'\n… i još {remaining_event_count} događaja.'
            if remaining_event_count
            else ''
        )
        return format_html(
            '<pre style="max-height:620px;overflow:auto;padding:14px;border:1px solid #ddd;'
            'border-radius:6px;background:#f8f8f8;white-space:pre-wrap">{}{}</pre>',
            rendered_events,
            suffix,
        )

    def save_model(self, request, calendar_import, form, change):
        uploaded_calendar_file = form.cleaned_data.get('calendar_file')
        validated_calendar_events = getattr(
            form,
            'validated_calendar_events',
            None,
        )
        if uploaded_calendar_file and validated_calendar_events is not None:
            prepare_calendar_import(
                calendar_import,
                calendar_events=validated_calendar_events,
                source_file_name=uploaded_calendar_file.name,
                imported_by=request.user,
            )
        super().save_model(request, calendar_import, form, change)
        if uploaded_calendar_file and validated_calendar_events is not None:
            replace_calendar_entries(
                calendar_import,
                validated_calendar_events,
            )
            clear_imported_calendar_cache(calendar_import.year)


@admin.register(LiturgicalCalendarEntry)
class LiturgicalCalendarEntryAdmin(ParishTechnicalAdminMixin, admin.ModelAdmin):
    list_display = (
        'date', 'name', 'liturgical_color', 'priority', 'is_primary',
        'calendar_year', 'calendar_provider',
    )
    list_filter = (
        'is_primary', 'liturgical_color', 'calendar_import__provider',
        'calendar_import__year',
    )
    search_fields = ('name', 'original_name', 'external_identifier')
    date_hierarchy = 'date'
    ordering = ('-date', '-is_primary', '-priority', 'name')
    readonly_fields = (
        'calendar_import', 'date', 'name', 'original_name',
        'liturgical_color', 'priority', 'priority_label', 'is_primary',
        'external_identifier', 'source_position', 'raw_data_preview',
    )
    fields = readonly_fields
    actions = None

    @admin.display(description='Godina', ordering='calendar_import__year')
    def calendar_year(self, calendar_entry):
        return calendar_entry.calendar_import.year

    @admin.display(description='Izvor', ordering='calendar_import__provider')
    def calendar_provider(self, calendar_entry):
        return calendar_entry.calendar_import.get_provider_display()

    @admin.display(description='Izvorni API zapis')
    def raw_data_preview(self, calendar_entry):
        rendered_data = json.dumps(
            calendar_entry.raw_data or {},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        return format_html(
            '<pre style="max-height:620px;overflow:auto;padding:14px;border:1px solid #ddd;'
            'border-radius:6px;background:#f8f8f8;white-space:pre-wrap">{}</pre>',
            rendered_data,
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return bool(obj is None and self.has_view_permission(request, obj))

    def has_delete_permission(self, request, obj=None):
        return False
