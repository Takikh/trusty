"""
Admin seeding script.

Usage:
    python -m app.seed_admin

Reads ADMIN_EMAIL and ADMIN_PASSWORD from .env and creates (or updates)
an admin user with role="admin", email_verified=True, admin_approved=True.
"""

from app.auth import hash_password
from app.config import settings
from app.database import rest


def seed() -> None:
    # Check if admin already exists
    result = (
        rest.from_("users")
        .select("*")
        .eq("email", settings.admin_email)
        .execute()
    )

    if result.data:
        # Update existing admin
        rest.from_("users").update({
            "password_hash": hash_password(settings.admin_password),
            "role": "admin",
            "email_verified": True,
            "admin_approved": True,
            "name": "System Admin",
        }).eq("email", settings.admin_email).execute()
        print(f"✔ Updated existing admin: {settings.admin_email}")
    else:
        # Create new admin
        rest.from_("users").insert({
            "email": settings.admin_email,
            "password_hash": hash_password(settings.admin_password),
            "name": "System Admin",
            "role": "admin",
            "email_verified": True,
            "admin_approved": True,
        }).execute()
        print(f"✔ Created admin: {settings.admin_email}")


if __name__ == "__main__":
    seed()
