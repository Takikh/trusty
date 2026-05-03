from django.contrib import admin

from interviews.models import ExpressionLog, InterviewSession, QALog


class QALogInline(admin.TabularInline):
    model = QALog
    extra = 0
    readonly_fields = ("created_at",)


class ExpressionLogInline(admin.TabularInline):
    model = ExpressionLog
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "subject_external_id", "user", "status", "active_turn_id", "created_at")
    list_filter = ("status",)
    inlines = (QALogInline, ExpressionLogInline)


@admin.register(QALog)
class QALogAdmin(admin.ModelAdmin):
    list_display = ("session", "turn_id", "role", "sequence", "created_at")


@admin.register(ExpressionLog)
class ExpressionLogAdmin(admin.ModelAdmin):
    list_display = ("session", "turn_id", "emotion", "confidence", "timestamp_ms")
