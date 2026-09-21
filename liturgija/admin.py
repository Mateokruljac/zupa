"""Django admin registracije za Liturgija."""
import json

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from liturgija.admin_forms import LiturgicalCalendarEntryForm
from liturgija.models import (
    LiturgicalCalendarEntry,
    LiturgicalTradition,
)
from liturgija.services.liturgical_imports import (
    manual_celebration_identity,
    refresh_primary_flags,
)
from liturgija.tasks import delete_calendar_entries_task, import_calendar_package_task
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


@admin.register(LiturgicalCalendarEntry)
class LiturgicalCalendarEntryAdmin(ParishTechnicalAdminMixin, admin.ModelAdmin):
    form = LiturgicalCalendarEntryForm
    change_list_template = (
        'admin/liturgija/liturgicalcalendarentry/change_list.html'
    )
    list_display = (
        'date', 'name', 'liturgical_color', 'priority', 'is_primary',
        'provider',
    )
    list_display_links = ('date', 'name')
    list_filter = ('is_primary', 'liturgical_color', 'provider')
    search_fields = ('name', 'original_name', 'external_identifier')
    date_hierarchy = 'date'
    ordering = ('-date', '-priority', 'name')
    readonly_fields = (
        'provider', 'external_identifier', 'is_primary',
        'raw_data_preview', 'created_at', 'updated_at',
    )
    fields = (
        'date', 'name', 'original_name', 'liturgical_color',
        'priority', 'priority_label', 'is_primary', 'provider',
        'external_identifier', 'raw_data_preview', 'created_at', 'updated_at',
    )

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

    def get_urls(self):
        return [
            path(
                'import/romcal/',
                self.admin_site.admin_view(self.import_romcal_view),
                name='liturgija_liturgicalcalendarentry_import_romcal',
            ),
            *super().get_urls(),
        ]

    def import_romcal_view(self, request):
        return self._import_year_view(
            request,
            title='Uvezi Romcal (Hrvatska)',
            help_text=(
                'Uvozi lokalni Romcal kalendar za Hrvatsku u pozadini (Celery), '
                'da HTTP zahtjev ne čeka generiranje kalendara. Hrvatski naziv i '
                'boja se uzimaju iz kataloga liturgijskih dana (latinski ključ). '
                'Na isti datum mogu stajati svagdan i svetac kao odvojeni retci. '
                'Postojeći redovi istog izvora se preskaču.'
            ),
            provider=LiturgicalCalendarEntry.Provider.ROMCAL_CROATIA,
        )

    def _import_year_view(self, request, *, title, help_text, provider):
        form = CalendarYearImportForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            year = form.cleaned_data['year']
            async_result = import_calendar_package_task.delay(provider, year)
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                payload = async_result.get()
                if payload.get('ok'):
                    messages.success(
                        request,
                        f'Uneseno {payload["created"]} redaka, preskočeno '
                        f'{payload["skipped"]} jer već postoje za taj izvor, '
                        'datum i slavlje.',
                    )
                else:
                    form.add_error('year', payload.get('error') or 'Uvoz nije uspio.')
                    return self._import_form_response(
                        request,
                        form,
                        title=title,
                        help_text=help_text,
                    )
            else:
                messages.info(
                    request,
                    f'Uvoz {year}. godine je pokrenut u pozadini. Osvježite '
                    'popis kad worker završi.',
                )
            return HttpResponseRedirect(
                reverse('admin:liturgija_liturgicalcalendarentry_changelist')
            )
        return self._import_form_response(
            request,
            form,
            title=title,
            help_text=help_text,
        )

    def _import_form_response(self, request, form, *, title, help_text):
        context = {
            **self.admin_site.each_context(request),
            'opts': self.opts,
            'form': form,
            'title': title,
            'import_help_text': help_text,
        }
        return TemplateResponse(
            request,
            'admin/liturgija/liturgicalcalendarentry/import_form.html',
            context,
        )

    def save_model(self, request, calendar_entry, form, change):
        previous_date = None
        if change:
            previous_date = (
                LiturgicalCalendarEntry.objects
                .filter(pk=calendar_entry.pk)
                .values_list('date', flat=True)
                .first()
            )
        else:
            calendar_entry.provider = LiturgicalCalendarEntry.Provider.MANUAL
        if calendar_entry.provider == LiturgicalCalendarEntry.Provider.MANUAL:
            calendar_entry.external_identifier = manual_celebration_identity(
                calendar_entry.date,
                calendar_entry.name,
            )
        super().save_model(request, calendar_entry, form, change)
        refresh_primary_flags({calendar_entry.date, previous_date})

    def has_delete_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_staff)

    def delete_model(self, request, calendar_entry):
        entry_date = calendar_entry.date
        super().delete_model(request, calendar_entry)
        refresh_primary_flags({entry_date})

    def delete_queryset(self, request, queryset):
        entry_ids = list(queryset.values_list('pk', flat=True))
        threshold = getattr(settings, 'ADMIN_ACTION_CELERY_THRESHOLD', 10_000)
        if len(entry_ids) > threshold:
            async_result = delete_calendar_entries_task.delay(entry_ids)
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                payload = async_result.get()
                messages.success(
                    request,
                    f'Obrisano {payload.get("deleted", 0)} zapisa.',
                )
            else:
                messages.info(
                    request,
                    f'Brisanje {len(entry_ids)} zapisa pokrenuto je u pozadini. '
                    'Osvježite popis kad worker završi.',
                )
            return
        entry_dates = set(queryset.values_list('date', flat=True))
        super().delete_queryset(request, queryset)
        refresh_primary_flags(entry_dates)
