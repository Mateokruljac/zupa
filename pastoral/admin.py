import json

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import format_html

from admin_interface.models import Theme

from pastoral.services.liturgical_imports import (
    clear_imported_calendar_cache,
    extract_calendar_events,
    prepare_calendar_import,
    replace_calendar_entries,
)

from .models import (
    AnointingDetails,
    BaptismDetails,
    ChurchEnrollment,
    ChurchSuiIuris,
    EcclesiasticalJurisdiction,
    EventParticipant,
    FormationCandidate,
    FormationProgramYear,
    FuneralDetails,
    GeneralRegisterEntry,
    LiturgicalCalendarEntry,
    LiturgicalCalendarImport,
    LiturgicalTradition,
    MarriageDetails,
    OtpChallenge,
    Parish,
    Person,
    RegisterBook,
    RegisterBookYear,
    RegisterEntry,
    RegisterTemplate,
    RegisterTemplateVersion,
    RegistryAuditEvent,
    SacramentalEvent,
)


try:
    admin.site.unregister(Theme)
except admin.sites.NotRegistered:
    pass


class ProtectedReferenceAdminMixin:
    def has_delete_permission(self, request, obj=None):
        return False


class SuperuserSensitiveAdminMixin:
    """Keep cross-tenant personal and audit data away from ordinary staff."""

    def has_module_permission(self, request):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_view_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_add_permission(self, request):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LiturgicalTradition)
class LiturgicalTraditionAdmin(ProtectedReferenceAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fields = ('id', 'name', 'code', 'is_active', 'created_at', 'updated_at')


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


@admin.register(Person)
class PersonAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = (
        'surname', 'given_names', 'date_of_birth', 'parish', 'status',
    )
    list_filter = ('status', 'sex', 'parish')
    search_fields = (
        'given_names', 'surname', 'birth_surname',
        'normalized_given_names', 'normalized_surname',
    )
    autocomplete_fields = ('parish', 'father', 'mother')
    readonly_fields = (
        'id', 'normalized_given_names', 'normalized_surname',
        'created_at', 'updated_at',
    )
    fields = (
        'id', 'parish', 'given_names', 'surname', 'birth_surname',
        'sex', 'date_of_birth', 'place_of_birth', 'father', 'mother', 'status',
        'normalized_given_names', 'normalized_surname', 'created_at', 'updated_at',
    )

    def save_model(self, request, person, form, change):
        person.full_clean()
        super().save_model(request, person, form, change)


@admin.register(ChurchEnrollment)
class ChurchEnrollmentAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = (
        'person', 'church_sui_iuris', 'parish', 'status',
        'valid_from', 'valid_until',
    )
    list_filter = ('status', 'church_sui_iuris', 'parish')
    search_fields = (
        'person__given_names', 'person__surname', 'decree_reference',
    )
    autocomplete_fields = (
        'parish', 'person', 'church_sui_iuris',
        'previous_enrollment', 'recorded_by',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    fields = (
        'id', 'parish', 'person', 'church_sui_iuris', 'status',
        'valid_from', 'valid_until', 'enrollment_basis', 'decree_reference',
        'previous_enrollment', 'recorded_by', 'created_at', 'updated_at',
    )

    def save_model(self, request, enrollment, form, change):
        if not enrollment.recorded_by_id:
            enrollment.recorded_by = request.user
        enrollment.full_clean()
        super().save_model(request, enrollment, form, change)


@admin.register(RegistryAuditEvent)
class RegistryAuditEventAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = (
        'occurred_at', 'event_type', 'parish', 'actor', 'outcome', 'target_type',
    )
    list_filter = ('outcome', 'event_type', 'parish', 'occurred_at')
    search_fields = (
        'event_type', 'parish__slug', 'actor__email',
        'target_id', 'correlation_id',
    )
    readonly_fields = (
        'id', 'parish', 'actor', 'event_type', 'target_type', 'target_id',
        'outcome', 'correlation_id', 'changed_fields', 'metadata', 'occurred_at',
    )
    fields = readonly_fields
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return bool(obj is None and self.has_view_permission(request, obj))


@admin.register(RegisterTemplate)
class RegisterTemplateAdmin(ProtectedReferenceAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'event_type', 'owner_scope', 'is_official', 'is_active')
    list_filter = ('event_type', 'owner_scope', 'is_official', 'is_active')
    search_fields = ('name', 'code')
    autocomplete_fields = ('church_sui_iuris', 'ecclesiastical_jurisdiction')
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


@admin.register(RegisterBook)
class RegisterBookAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = (
        'title', 'registry_type', 'parish', 'status',
        'year_from', 'year_until', 'template_version',
    )
    list_filter = (
        'registry_type', 'status', 'parish',
        'template_version__template__event_type',
    )
    search_fields = (
        'title', 'volume', 'public_identifier', 'parish__slug',
    )
    autocomplete_fields = ('parish', 'template_version')
    readonly_fields = ('id', 'created_at', 'updated_at')

    def save_model(self, request, register_book, form, change):
        register_book.full_clean()
        super().save_model(request, register_book, form, change)


@admin.register(RegisterBookYear)
class RegisterBookYearAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = ('register_book', 'year', 'status', 'next_entry_number')
    list_filter = ('status', 'year', 'register_book__parish')
    search_fields = ('register_book__title', 'register_book__parish__slug')
    autocomplete_fields = ('register_book',)
    readonly_fields = ('id',)


@admin.register(SacramentalEvent)
class SacramentalEventAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = ('event_type', 'event_date', 'parish', 'status', 'source')
    list_filter = ('event_type', 'status', 'source', 'parish')
    search_fields = ('minister_name', 'parish__slug')
    autocomplete_fields = (
        'parish', 'celebrating_parish', 'minister', 'liturgical_tradition',
        'created_by', 'updated_by',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')

    def save_model(self, request, sacramental_event, form, change):
        sacramental_event.full_clean()
        super().save_model(request, sacramental_event, form, change)


@admin.register(EventParticipant)
class EventParticipantAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = ('event', 'role', 'person', 'historical_name', 'parish')
    list_filter = ('role', 'parish')
    search_fields = ('historical_name', 'person__given_names', 'person__surname')
    autocomplete_fields = ('parish', 'event', 'person')
    readonly_fields = ('id',)

    def save_model(self, request, participant, form, change):
        participant.full_clean()
        super().save_model(request, participant, form, change)


@admin.register(BaptismDetails)
class BaptismDetailsAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = ('event', 'godparent_certificate_received')
    list_filter = ('godparent_certificate_received',)
    autocomplete_fields = ('event',)


@admin.register(MarriageDetails)
class MarriageDetailsAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = (
        'couple_display_name', 'event', 'operational_status',
        'documents_complete', 'stipend_paid',
    )
    list_filter = ('operational_status', 'documents_complete', 'stipend_paid')
    search_fields = (
        'couple_display_name', 'contact', 'witnesses_name',
        'event__public_identifier',
    )
    autocomplete_fields = ('event',)


@admin.register(FuneralDetails)
class FuneralDetailsAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = (
        'event', 'death_date', 'mass_planned', 'operational_status',
        'stipend_paid',
    )
    list_filter = ('mass_planned', 'operational_status', 'stipend_paid')
    search_fields = (
        'family_contact', 'cemetery_location', 'event__public_identifier',
        'event__participants__historical_name',
    )
    autocomplete_fields = ('event',)


@admin.register(AnointingDetails)
class AnointingDetailsAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = (
        'event', 'operational_status', 'completed', 'scheduled_time',
    )
    list_filter = ('operational_status', 'completed')
    search_fields = (
        'address', 'location', 'contact', 'event__public_identifier',
        'event__participants__historical_name',
    )
    autocomplete_fields = ('event',)


@admin.register(FormationProgramYear)
class FormationProgramYearAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = (
        'program_type', 'year', 'parish', 'group_name', 'ceremony_date',
        'contribution_paid',
    )
    list_filter = ('program_type', 'year', 'contribution_paid', 'parish')
    search_fields = (
        'public_identifier', 'group_name', 'celebrant_name', 'parish__slug',
    )
    autocomplete_fields = ('parish',)
    readonly_fields = ('id', 'public_identifier', 'created_at', 'updated_at')


@admin.register(FormationCandidate)
class FormationCandidateAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = (
        'historical_name', 'program_year', 'school_name', 'school_class',
        'operational_status', 'contribution_paid',
    )
    list_filter = (
        'program_year__program_type', 'program_year__year',
        'operational_status', 'contribution_paid', 'program_year__parish',
    )
    search_fields = (
        'historical_name', 'given_names', 'surname', 'school_name',
        'parents_name', 'sponsor_name', 'public_identifier',
    )
    autocomplete_fields = ('program_year', 'person', 'sacramental_event')
    readonly_fields = ('id', 'public_identifier', 'created_at', 'updated_at')


@admin.register(RegisterEntry)
class RegisterEntryAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = ('entry_reference', 'entry_number', 'register_book_year', 'parish', 'status')
    list_filter = ('status', 'parish', 'register_book_year__year')
    search_fields = ('entry_reference', 'parish__slug')
    autocomplete_fields = (
        'parish', 'register_book_year', 'event', 'template_version',
        'previous_entry', 'created_by', 'updated_by',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')

    def save_model(self, request, register_entry, form, change):
        register_entry.full_clean()
        super().save_model(request, register_entry, form, change)


@admin.register(GeneralRegisterEntry)
class GeneralRegisterEntryAdmin(SuperuserSensitiveAdminMixin, admin.ModelAdmin):
    list_display = (
        'registry_reference', 'subject_name', 'record_date',
        'register_book_year', 'operational_status',
    )
    list_filter = (
        'operational_status', 'record_date',
        'register_book_year__register_book__parish',
    )
    search_fields = (
        'registry_reference', 'subject_name', 'place',
        'responsible_name', 'public_identifier',
    )
    autocomplete_fields = ('register_book_year',)
    readonly_fields = ('id', 'public_identifier', 'created_at', 'updated_at')


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


@admin.register(Parish)
class ParishAdmin(admin.ModelAdmin):
    list_display = (
        'display_name', 'slug', 'tenant_id', 'lifecycle_status', 'diocese',
        'church_sui_iuris', 'ecclesiastical_jurisdiction',
        'record_count', 'data_size', 'updated_at',
    )
    list_filter = (
        'lifecycle_status', 'diocese', 'church_sui_iuris',
        'ecclesiastical_jurisdiction', 'default_liturgical_tradition',
    )
    search_fields = ('slug',)
    autocomplete_fields = (
        'diocese', 'church_sui_iuris', 'ecclesiastical_jurisdiction',
        'default_liturgical_tradition',
    )
    readonly_fields = (
        'tenant_id', 'updated_at', 'record_count', 'data_size',
        'settings_preview', 'data_preview',
    )
    fields = (
        'tenant_id', 'slug', 'diocese', 'church_sui_iuris',
        'ecclesiastical_jurisdiction', 'default_liturgical_tradition',
        'lifecycle_status',
        'updated_at', 'record_count', 'data_size',
        'settings_preview', 'data_preview',
    )
    actions = None

    @admin.display(description='Župa', ordering='slug')
    def display_name(self, obj):
        return obj.settings.get('name') or obj.slug

    @admin.display(description='Broj zapisa')
    def record_count(self, obj):
        return sum(len(value) for value in (obj.data or {}).values() if isinstance(value, list))

    @admin.display(description='Veličina JSON-a')
    def data_size(self, obj):
        size = len(json.dumps(obj.data or {}, ensure_ascii=False).encode('utf-8'))
        return f'{size / 1024:.1f} KB'

    @admin.display(description='Postavke — samo pregled')
    def settings_preview(self, obj):
        return self._json_preview(obj.settings)

    @admin.display(description='Podatkovna jezgra — samo pregled')
    def data_preview(self, obj):
        return self._json_preview(obj.data, max_height=620)

    @staticmethod
    def _json_preview(value, max_height=360):
        rendered = json.dumps(value or {}, ensure_ascii=False, indent=2, sort_keys=True)
        return format_html(
            '<pre style="max-height:{}px;overflow:auto;padding:14px;border:1px solid #ddd;'
            'border-radius:6px;background:#f8f8f8;white-space:pre-wrap">{}</pre>',
            max_height,
            rendered,
        )

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, parish, form, change):
        parish.full_clean()
        super().save_model(request, parish, form, change)


@admin.register(OtpChallenge)
class OtpChallengeAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'status_label', 'failed_attempts', 'created_at')
    list_filter = ('used', 'role', 'created_at')
    search_fields = ('email',)
    date_hierarchy = 'created_at'
    readonly_fields = (
        'email', 'role', 'status_label', 'failed_attempts',
        'used', 'locked_at', 'created_at', 'expires_at',
    )
    fields = (
        'email', 'role', 'status_label', 'failed_attempts',
        'used', 'locked_at', 'created_at', 'expires_at',
    )
    actions = None

    @admin.display(description='Status')
    def status_label(self, obj):
        if obj.used:
            return 'Zaključan' if obj.locked_at else 'Iskorišten'
        return 'Istekao' if timezone.now() >= obj.expires_at else 'Aktivan'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return bool(obj is None and super().has_change_permission(request, obj))

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LiturgicalCalendarImport)
class LiturgicalCalendarImportAdmin(admin.ModelAdmin):
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
class LiturgicalCalendarEntryAdmin(admin.ModelAdmin):
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

    def has_delete_permission(self, request, obj=None):
        return False
