import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="InterviewSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("subject_external_id", models.CharField(db_index=True, max_length=255)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("live", "Live"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=32)),
                ("active_turn_id", models.CharField(blank=True, max_length=64, null=True)),
                ("rag_context", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="interview_sessions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "interviews_session",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="QALog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("turn_id", models.CharField(db_index=True, max_length=64)),
                ("role", models.CharField(help_text="e.g. assistant, user, system", max_length=16)),
                ("content", models.TextField()),
                ("sequence", models.PositiveIntegerField(default=0)),
                ("extra", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="qa_logs", to="interviews.interviewsession")),
            ],
            options={
                "db_table": "interviews_qa_log",
                "ordering": ["session", "sequence", "created_at"],
            },
        ),
        migrations.CreateModel(
            name="ExpressionLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("turn_id", models.CharField(db_index=True, max_length=64)),
                ("emotion", models.CharField(max_length=64)),
                ("confidence", models.FloatField()),
                ("timestamp_ms", models.BigIntegerField()),
                ("raw", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="expression_logs", to="interviews.interviewsession")),
            ],
            options={
                "db_table": "interviews_expression_log",
                "ordering": ["session", "timestamp_ms", "created_at"],
            },
        ),
    ]
