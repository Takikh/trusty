"""
Interview state for Phase 4 (real-time AI video interview).

REFACTOR NOTE (critical for multi-tenant production):
------------------------------------------------------
The legacy `ia/` package persists interview progress in local files:
  - `ia/runtime/interview_state.json`  (see `ia/pipeline/runtime_state.py`)
  - `ia/runtime/expression_log.jsonl`  (expression monitor / DeepFace path)

That pattern is single-user and not safe under concurrent web traffic.

When you wire the WebSocket consumer and Celery/HTTP flows to the AI layer,
you MUST refactor `ia/pipeline/runtime_state.py`, `ia/pipeline/interview.py`,
and `ia/pipeline/expression.py` so they accept in-memory / DB-backed state
instead of reading or writing those paths.

Pass these model instances (or their primary keys + thin adapter objects)
into the refactored ia functions:
  - InterviewSession — replaces interview_state.json (doctor/session identity,
    active turn, RAG context pointer, status).
  - QALog — append-only transcript rows per turn (replaces embedding Q&A only
    in JSON files where applicable).
  - ExpressionLog — one row per DeepFace sample (replaces expression_log.jsonl).

Do not open shared JSON files from request handlers or channel workers.
"""
import uuid

from django.conf import settings
from django.db import models


class InterviewSession(models.Model):
    """
    One live or completed interview; correlates WebSocket connections and logs.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        LIVE = "live", "Live"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_sessions",
    )
    # External subject identifier (e.g. doctor_id in ia/main.py terminology).
    subject_external_id = models.CharField(max_length=255, db_index=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    # Mirrors `active_turn_id` from ia/pipeline/runtime_state.py — set from DB only.
    active_turn_id = models.CharField(max_length=64, null=True, blank=True)
    # Serialized RAG / survey context blob or reference; keep flexible until ia is refactored.
    rag_context = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "interviews_session"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"InterviewSession({self.id}, {self.subject_external_id})"


class QALog(models.Model):
    """Structured Q&A / transcript lines for an interview (per turn or message)."""

    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name="qa_logs",
    )
    turn_id = models.CharField(max_length=64, db_index=True)
    role = models.CharField(
        max_length=16,
        help_text="e.g. assistant, user, system",
    )
    content = models.TextField()
    sequence = models.PositiveIntegerField(default=0)
    extra = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "interviews_qa_log"
        ordering = ["session", "sequence", "created_at"]

    def __str__(self) -> str:
        return f"QALog({self.session_id}, {self.turn_id}, {self.role})"


class ExpressionLog(models.Model):
    """
    DeepFace / expression samples associated with an interview session.
    Replaces append-only JSONL files for multi-worker deployments.
    """

    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name="expression_logs",
    )
    turn_id = models.CharField(max_length=64, db_index=True)
    emotion = models.CharField(max_length=64)
    confidence = models.FloatField()
    timestamp_ms = models.BigIntegerField()
    raw = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "interviews_expression_log"
        ordering = ["session", "timestamp_ms", "created_at"]

    def __str__(self) -> str:
        return f"ExpressionLog({self.session_id}, {self.emotion})"
