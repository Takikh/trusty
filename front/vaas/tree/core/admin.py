from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from core.models import ClientAPIKey, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (("Organization", {"fields": ("organization_name",)}),)
    list_display = ("username", "email", "organization_name", "is_staff")


@admin.register(ClientAPIKey)
class ClientAPIKeyAdmin(admin.ModelAdmin):
    list_display = ("name", "key_prefix", "user", "is_active", "created_at", "last_used_at")
    list_filter = ("is_active",)
    readonly_fields = ("key_prefix", "key_hash", "created_at", "last_used_at")
