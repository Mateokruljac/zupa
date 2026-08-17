from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User


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
class UserAdmin(DjangoUserAdmin):
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
            'description': 'Staff status otvara tehničku administraciju; poslovna uloga određuje pristup Pastoral sučelju.',
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
