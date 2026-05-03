"""
WebSocket consumer for Phase 4 — binary audio (STT → LLM → TTS) and video frames (DeepFace).

REFACTOR NOTE:
--------------
`ia/pipeline/expression.ExpressionStream` today reads a webcam in a thread and uses
`runtime_state` files. In production, feed frames from the client via this consumer
and persist results with `ExpressionLog` rows on `InterviewSession` instead of JSONL.

`ia/audio/stt_whisper/stt.py` is microphone-oriented; add a bytes/PCM code path or
call faster-whisper directly on buffered audio from the browser.
"""
import json
from typing import Any
from uuid import UUID

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from interviews.models import InterviewSession


class InterviewConsumer(AsyncWebsocketConsumer):
    """
    Accepts:
      - Binary messages: raw audio chunks (PCM or encoded — define contract with frontend).
      - Text messages: JSON control frames, e.g. video frames as base64 or metadata.
    """

    async def connect(self):
        raw_session = self.scope["url_route"]["kwargs"].get("session_id")
        try:
            UUID(str(raw_session))
        except ValueError:
            await self.close(code=4400)
            return

        self.session_id = str(raw_session)
        self.user = self.scope.get("user")

        @database_sync_to_async
        def _load_session():
            try:
                return InterviewSession.objects.get(pk=self.session_id)
            except InterviewSession.DoesNotExist:
                return None

        self.interview_session = await _load_session()
        if self.interview_session is None:
            await self.close(code=4404)
            return

        await self.channel_layer.group_add(self._group_name(), self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self._group_name(), self.channel_name)

    def _group_name(self) -> str:
        return f"interview_{self.session_id}"

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data is not None:
            await self._handle_binary_audio(bytes_data)
            return

        if text_data:
            try:
                payload = json.loads(text_data)
            except json.JSONDecodeError:
                await self.send(text_data=json.dumps({"error": "invalid_json"}))
                return
            await self._handle_text_frame(payload)

    async def _handle_text_frame(self, payload: dict[str, Any]):
        msg_type = payload.get("type")
        if msg_type == "video_frame":
            # Expect base64 JPEG/PNG or raw dimensions + frame reference per your client.
            frame_b64 = payload.get("data")
            if frame_b64:
                await self._handle_video_frame_b64(frame_b64)
        elif msg_type == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))

    async def _handle_binary_audio(self, chunk: bytes):
        """
        Buffer or stream into your STT pipeline.
        TODO: import and call STT on accumulated utterance, e.g. after VAD/silence:
          from audio.stt_whisper import stt as ia_stt
          # ia_stt expects microphone today — refactor to accept bytes/BytesIO.
        """
        await self._placeholder_stt_from_audio_chunk(chunk)

    async def _handle_video_frame_b64(self, frame_b64: str):
        """
        Decode frame and run DeepFace emotion path.
        TODO: import and call expression analysis, e.g.:
          from pipeline import expression as ia_expression
          # Refactor ia_expression to analyze a single numpy frame (no cv2.VideoCapture).
        """
        await self._placeholder_expression_from_frame(frame_b64)

    async def _placeholder_stt_from_audio_chunk(self, chunk: bytes):
        """Replace with ia audio STT (Whisper) after adding a non-mic entrypoint."""
        _ = chunk  # silence lint until wired

    async def _placeholder_expression_from_frame(self, frame_b64: str):
        """Replace with ia.pipeline.expression (DeepFace) on decoded image array."""
        _ = frame_b64
