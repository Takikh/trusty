from django.urls import re_path

from interviews.consumers import InterviewConsumer

websocket_urlpatterns = [
    re_path(
        r"^ws/interview/(?P<session_id>[0-9a-f-]{36})/$",
        InterviewConsumer.as_asgi(),
    ),
]
