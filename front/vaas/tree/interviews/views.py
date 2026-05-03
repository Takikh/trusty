from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from interviews.models import InterviewSession


class InterviewSessionCreateView(APIView):
    """Create an InterviewSession and return its UUID (Phase 4 WebSocket setup)."""

    def post(self, request):
        doctor_id = request.data.get("doctor_id") or request.data.get("subject_external_id")
        if not doctor_id or not str(doctor_id).strip():
            return Response(
                {"detail": "doctor_id (or subject_external_id) is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = InterviewSession.objects.create(
            user=request.user,
            subject_external_id=str(doctor_id).strip(),
            status=InterviewSession.Status.PENDING,
        )
        return Response(
            {
                "session_uuid": str(session.id),
                "subject_external_id": session.subject_external_id,
                "status": session.status,
            },
            status=status.HTTP_201_CREATED,
        )
