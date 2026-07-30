from django.contrib import admin

from .models import User


# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_filter = ['role', 'last_login']
    list_display = ['email', 'name', 'role', 'is_staff']
    list_per_page = 20


# admin.site.site_url = 'https://www.config.com'
admin.site.register(User, UserAdmin)
