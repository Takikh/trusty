from django.urls import path

from verification.views import HealthView, VerificationDecisionView, VerificationUploadView

urlpatterns = [
    path("health/", HealthView.as_view(), name="api-health"),
    path("v1/verification/upload/", VerificationUploadView.as_view(), name="verification-upload"),
    path(
        "v1/verification/jobs/<uuid:job_id>/decision/",
        VerificationDecisionView.as_view(),
        name="verification-decision",
    ),
]
