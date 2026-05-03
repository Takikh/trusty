"""
Pydantic schemas for request/response validation.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ─────────────────────────────────────────────────────────────────────────
# Auth — Requests
# ─────────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    """Step 1 of doctor registration."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=320)
    password: str = Field(..., min_length=6, max_length=128)


class VerifyCodeRequest(BaseModel):
    """Step 2 — submit the 6-digit OTP."""
    email: str
    code: str = Field(..., min_length=6, max_length=6)


class LoginRequest(BaseModel):
    """Doctor or Admin login."""
    email: str
    password: str


# ─────────────────────────────────────────────────────────────────────────
# Auth — Responses
# ─────────────────────────────────────────────────────────────────────────
class UserResponse(BaseModel):
    """Public user representation (never includes password)."""
    id: uuid.UUID
    email: str
    name: str
    role: str
    email_verified: bool
    admin_approved: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Returned after successful login."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic success / info message."""
    message: str


# ─────────────────────────────────────────────────────────────────────────
# Admin — Responses
# ─────────────────────────────────────────────────────────────────────────
class DoctorListItem(BaseModel):
    """
    A doctor as seen by the Admin dashboard.  Combines auth data from
    the `users` table with verification data from the `doctors` table.
    """
    # From users table
    id: uuid.UUID
    email: str
    name: str
    email_verified: bool
    admin_approved: bool
    created_at: datetime | None = None

    # From doctors table (may be None if the doctor hasn't started the pipeline)
    pipeline_status: str | None = None
    verdict: str | None = None
    final_score: float | None = None
    is_verified_by_service: bool = False

    model_config = {"from_attributes": True}


class AdminApprovalRequest(BaseModel):
    """Toggle admin_approved on a doctor's user record."""
    admin_approved: bool
