import hashlib
import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Application user; extend with org metadata as needed."""

    organization_name = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "core_user"


class ClientAPIKey(models.Model):
    """
    API keys for programmatic client access (VaaS integrations).
    Store only a hash of the secret; show the raw key once at creation.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    name = models.CharField(max_length=128, help_text="Label for this key (e.g. partner name).")
    key_prefix = models.CharField(max_length=16, db_index=True)
    key_hash = models.CharField(max_length=64, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "core_client_api_key"
        ordering = ["-created_at"]

    @staticmethod
    def hash_secret(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    def generate_raw_key(cls) -> str:
        return f"vaas_{secrets.token_urlsafe(32)}"

    @classmethod
    def create_for_user(cls, user: "User", name: str) -> tuple["ClientAPIKey", str]:
        raw = cls.generate_raw_key()
        prefix = raw[:12]
        return (
            cls.objects.create(
                user=user,
                name=name,
                key_prefix=prefix,
                key_hash=cls.hash_secret(raw),
            ),
            raw,
        )
