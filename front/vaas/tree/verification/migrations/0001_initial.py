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
            name="VerificationJob",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("subject_external_id", models.CharField(db_index=True, max_length=255)),
                ("status", models.CharField(choices=[("queued", "Queued"), ("processing", "Processing"), ("succeeded", "Succeeded"), ("failed", "Failed")], default="queued", max_length=32)),
                ("celery_task_id", models.CharField(blank=True, max_length=255)),
                ("result", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="verification_jobs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "verification_job",
                "ordering": ["-created_at"],
            },
        ),
    ]
