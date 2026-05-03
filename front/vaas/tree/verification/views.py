import uuid

from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.authentication import APIKeyAuthentication
from verification.models import VerificationJob


class HealthView(APIView):
    """
    Authenticated health check — validates X-Api-Key (or session) for Postman / probes.
    """

    authentication_classes = [APIKeyAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "status": "ok",
                "service": "vaas",
                "authenticated_user": request.user.username,
            }
        )


class VerificationUploadView(APIView):
    """Phase 1 — accept PDF upload and create a VerificationJob (session_uuid = job id)."""

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        doctor_id = request.data.get("doctor_id")
        upload = request.FILES.get("file")
        if not doctor_id or not str(doctor_id).strip():
            return Response(
                {"detail": "doctor_id is required (form field)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not upload:
            return Response(
                {"detail": "file is required (PDF, form field name: file)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job = VerificationJob.objects.create(
            user=request.user,
            subject_external_id=str(doctor_id).strip(),
            status=VerificationJob.Status.QUEUED,
        )
        safe_name = upload.name.replace("..", "").replace("\\", "").replace("/", "") or "upload.pdf"
        storage_path = f"verification/{job.id}/{safe_name}"
        default_storage.save(storage_path, upload)

        job.result = {
            "pdf_storage_path": storage_path,
            "original_filename": getattr(upload, "name", safe_name),
        }
        job.save(update_fields=["result", "updated_at"])

        return Response(
            {
                "session_uuid": str(job.id),
                "job_id": str(job.id),
                "subject_external_id": job.subject_external_id,
                "status": job.status,
                "message": "Job created. Wire Celery (pdf_to_images_task / ocr_images_task) to populate decision.",
            },
            status=status.HTTP_201_CREATED,
        )


class VerificationDecisionView(APIView):
    """Final decision / status once AI pipeline updates VerificationJob.result."""

    def get(self, request, job_id):
        try:
            uuid.UUID(str(job_id))
        except ValueError:
            return Response({"detail": "Invalid job id."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = VerificationJob.objects.get(pk=job_id, user=request.user)
        except VerificationJob.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        result = job.result or {}
        decision = result.get("decision")
        if decision is None:
            if job.status == VerificationJob.Status.FAILED:
                decision = "rejected"
            elif job.status == VerificationJob.Status.SUCCEEDED:
                decision = result.get("final_decision", "approved")
            else:
                decision = "pending"

        return Response(
            {
                "session_uuid": str(job.id),
                "job_status": job.status,
                "decision": decision,
                "result": result,
                "error_message": job.error_message or None,
            }
        )
