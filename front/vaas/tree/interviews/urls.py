from django.urls import path

from interviews.views import InterviewSessionCreateView

urlpatterns = [
    path("v1/interviews/sessions/", InterviewSessionCreateView.as_view(), name="interview-session-create"),
]
