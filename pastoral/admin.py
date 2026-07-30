from django.contrib import admin

from .models import OtpChallenge, Parish


@admin.register(Parish)
class ParishAdmin(admin.ModelAdmin):
    list_display = ('slug', 'updated_at')
    readonly_fields = ('updated_at',)


@admin.register(OtpChallenge)
class OtpChallengeAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'code', 'used', 'created_at')
    list_filter = ('used', 'role')
