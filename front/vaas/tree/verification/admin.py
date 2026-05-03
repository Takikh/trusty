from django.contrib import admin

from verification.models import VerificationJob


@admin.register(VerificationJob)
class VerificationJobAdmin(admin.ModelAdmin):
    list_display = ("id", "subject_external_id", "user", "status", "created_at")
    list_filter = ("status",)
