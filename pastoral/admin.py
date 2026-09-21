import json

from django import forms
from django.contrib import admin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from admin_interface.models import Theme

from pastoral.admin_mixins import (
    ParishTechnicalAdminMixin,
    ProtectedReferenceAdminMixin,
)
from django_multitenant.schema import with_tenant_schema
from pastoral.models import Diocese, Parish, User

try:
    admin.site.unregister(Theme)
except admin.sites.NotRegistered:
    pass


@admin.register(Diocese)
class DioceseAdmin(ProtectedReferenceAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fields = ('id', 'name', 'code', 'is_active', 'created_at', 'updated_at')


@admin.register(Parish)
class ParishAdmin(ParishTechnicalAdminMixin, admin.ModelAdmin):
    """Postavke župe — ne dnevni pastoralni unos."""

    list_display = (
        'display_name', 'slug', 'tenant_id', 'lifecycle_status', 'diocese',
        'canonical_tradition', 'ecclesiastical_jurisdiction',
        'updated_at',
    )
    list_filter = (
        'lifecycle_status', 'diocese', 'canonical_tradition',
        'ecclesiastical_jurisdiction', 'default_liturgical_tradition',
    )
    search_fields = ('slug',)
    autocomplete_fields = (
        'diocese', 'ecclesiastical_jurisdiction',
        'default_liturgical_tradition',
    )
    readonly_fields = (
        'tenant_id', 'updated_at', 'settings_preview',
    )
    fields = (
        'tenant_id', 'slug', 'diocese', 'canonical_tradition',
        'ecclesiastical_jurisdiction', 'default_liturgical_tradition',
        'lifecycle_status',
        'updated_at', 'settings_preview',
    )
    actions = None

    @admin.display(description='Župa', ordering='slug')
    def display_name(self, obj):
        return obj.settings.get('name') or obj.slug

    @admin.display(description='Postavke — samo pregled')
    def settings_preview(self, obj):
        rendered = json.dumps(
            obj.settings or {},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        return format_html(
            '<pre style="max-height:360px;overflow:auto;padding:14px;border:1px solid #ddd;'
            'border-radius:6px;background:#f8f8f8;white-space:pre-wrap">{}</pre>',
            rendered,
        )

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, parish, form, change):
        parish.full_clean()
        super().save_model(request, parish, form, change)


class AdminUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Lozinka', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Potvrda lozinke', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'name', 'role', 'is_active', 'is_staff')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Lozinke se ne podudaraju.')
        if password2:
            validate_password(password2, self.instance)
        return password2

    @with_tenant_schema
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class AdminUserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label='Lozinka')

    class Meta:
        model = User
        fields = '__all__'

    def clean_password(self):
        return self.initial.get('password')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    add_form = AdminUserCreationForm
    form = AdminUserChangeForm
    model = User
    ordering = ('email',)
    search_fields = ('email', 'name', 'phone_number')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'last_login')
    list_display = ('email', 'name', 'role', 'is_active', 'is_staff', 'last_login')
    list_per_page = 20
    readonly_fields = ('id', 'last_login')
    fieldsets = (
        ('Identitet', {'fields': ('id', 'email', 'password', 'name', 'role')}),
        ('Kontakt', {'fields': ('address', 'phone_number', 'date_of_birth')}),
        ('Pristup Django administraciji', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': (
                'Staff status otvara tehničku administraciju župe '
                '(periodična konfiguracija). Poslovna uloga određuje pristup Pastoralu.'
            ),
        }),
        ('Aktivnost', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        ('Novi korisnik', {
            'classes': ('wide',),
            'fields': (
                'email', 'name', 'role', 'password1', 'password2',
                'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
            ),
        }),
    )

    def has_module_permission(self, request):
        return bool(request.user.is_active and request.user.is_staff)

    def has_view_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_staff)

    def has_add_permission(self, request):
        return bool(request.user.is_active and request.user.is_staff)

    def has_change_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_staff)

    def has_delete_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_superuser)
