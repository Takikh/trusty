"""
Admin-only routes — doctor management dashboard endpoints.

All routes require a valid JWT with role="admin".
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import require_admin
from app.database import rest
from app.schemas import AdminApprovalRequest, DoctorListItem, MessageResponse, UserResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/doctors", response_model=list[DoctorListItem])
def list_doctors(_admin: dict = Depends(require_admin)):
    """
    Return all registered doctor users, enriched with their pipeline
    verification status from the `doctors` table (linked by email).
    """
    # Fetch all doctor-role users
    users_result = (
        rest.from_("users")
        .select("*")
        .eq("role", "doctor")
        .order("created_at", desc=True)
        .execute()
    )
    users = users_result.data or []

    # Fetch all doctor pipeline records for cross-reference
    doctors_result = rest.from_("doctors").select("*").execute()
    doctors_by_email: dict[str, dict] = {
        d["email"]: d for d in (doctors_result.data or [])
    }

    items: list[DoctorListItem] = []
    for user in users:
        doc = doctors_by_email.get(user["email"])
        items.append(
            DoctorListItem(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                email_verified=user["email_verified"],
                admin_approved=user["admin_approved"],
                created_at=user.get("created_at"),
                pipeline_status=doc["status"] if doc else None,
                verdict=doc["verdict"] if doc else None,
                final_score=doc["final_score"] if doc else None,
                is_verified_by_service=(doc.get("verdict") == "VERIFIED") if doc else False,
            )
        )

    return items


@router.patch(
    "/doctors/{user_id}/approval",
    response_model=UserResponse,
)
def update_doctor_approval(
    user_id: str,
    body: AdminApprovalRequest,
    _admin: dict = Depends(require_admin),
):
    """
    Toggle admin_approved on a doctor's user record.
    The admin has the final say on account activation.
    """
    # Verify doctor exists
    result = (
        rest.from_("users")
        .select("*")
        .eq("id", user_id)
        .eq("role", "doctor")
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor user not found.",
        )

    # Update approval status
    updated = (
        rest.from_("users")
        .update({"admin_approved": body.admin_approved})
        .eq("id", user_id)
        .execute()
    )

    return UserResponse(**updated.data[0])
