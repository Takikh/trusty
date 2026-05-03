"""
Authentication routes — registration (2-step with OTP), login, and /me.
"""

import random
import string
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database import rest
from app.email_service import send_verification_email
from app.schemas import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    VerifyCodeRequest,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP of the given length."""
    return "".join(random.choices(string.digits, k=length))


# ─────────────────────────────────────────────────────────────────────────
# STEP 1: Register — create user + send OTP
# ─────────────────────────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(body: RegisterRequest):
    """
    Create a new doctor account (email_verified=False, admin_approved=False)
    and send a 6-digit verification code to their email.
    """
    # Check for existing user with the same email
    existing = (
        rest.from_("users")
        .select("id")
        .eq("email", body.email)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Create user
    rest.from_("users").insert({
        "email": body.email,
        "password_hash": hash_password(body.password),
        "name": f"{body.first_name} {body.last_name}",
        "role": "doctor",
        "email_verified": False,
        "admin_approved": False,
    }).execute()

    # Generate and store OTP with 10-min expiry
    code = _generate_otp()
    expires = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

    rest.from_("verification_codes").insert({
        "email": body.email,
        "code": code,
        "expires_at": expires,
        "used": False,
    }).execute()

    # Send OTP email
    try:
        send_verification_email(body.email, code)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification email: {exc}",
        )

    return MessageResponse(message="Verification code sent to your email.")


# ─────────────────────────────────────────────────────────────────────────
# STEP 2: Verify email — validate OTP
# ─────────────────────────────────────────────────────────────────────────
@router.post("/verify-email", response_model=MessageResponse)
def verify_email(body: VerifyCodeRequest):
    """
    Validate the 6-digit OTP.  On success, set email_verified=True.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Find valid, unused code
    result = (
        rest.from_("verification_codes")
        .select("*")
        .eq("email", body.email)
        .eq("code", body.code)
        .eq("used", False)
        .gte("expires_at", now)
        .order("expires_at", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code.",
        )

    otp_record = result.data[0]

    # Mark code as used
    rest.from_("verification_codes").update({
        "used": True,
    }).eq("id", otp_record["id"]).execute()

    # Mark user as email-verified
    user_result = (
        rest.from_("users")
        .select("id")
        .eq("email", body.email)
        .execute()
    )
    if not user_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    rest.from_("users").update({
        "email_verified": True,
    }).eq("email", body.email).execute()

    return MessageResponse(message="Email verified successfully.")


# ─────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    """
    Authenticate with email + password.

    Checks:
    1. Credentials valid
    2. Email verified
    3. Admin approved (for doctors)

    Returns a JWT on success.
    """
    result = (
        rest.from_("users")
        .select("*")
        .eq("email", body.email)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user = result.data[0]

    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user["email_verified"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address first.",
        )

    # Admin users bypass the admin_approved check
    if user["role"] != "admin" and not user["admin_approved"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending administrative approval.",
        )

    token = create_access_token(data={"sub": user["id"], "role": user["role"]})

    return TokenResponse(
        access_token=token,
        user=UserResponse(**user),
    )


# ─────────────────────────────────────────────────────────────────────────
# GET /me
# ─────────────────────────────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserResponse(**current_user)
