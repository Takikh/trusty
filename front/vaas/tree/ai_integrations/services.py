"""
Logical facades over the existing `ia/` package (no HTTP models here).

All imports from `pipeline`, `audio`, etc. assume `sys.path` includes the `ia/`
directory (configured in `vaas_project.settings`).

When you refactor `ia` for DB-backed interview state, add adapter functions here
that accept Django model instances and delegate to the updated ia callables.
"""
from __future__ import annotations

from typing import Any


def pdf_to_images(pdf_paths: list[str], doctor_id: str, output_dir: str) -> list[dict[str, Any]]:
    from pipeline.pdf_to_images import pdf_to_images as _pdf_to_images

    return _pdf_to_images(pdf_paths, doctor_id, output_dir)


def run_ocr(image_paths: list[str]) -> str:
    from pipeline.ocr import run_ocr as _run_ocr

    return _run_ocr(image_paths)


def stt_whisper_placeholder():
    """
    Re-export boundary for Whisper STT (`ia.audio.stt_whisper.stt`).
    The current ia module targets microphone capture; expose a bytes-based API here
    after refactoring ia.
    """
    from audio.stt_whisper import stt as ia_stt  # noqa: F401

    return ia_stt


def expression_placeholder():
    """Boundary for DeepFace expression (`ia.pipeline.expression`)."""
    from pipeline import expression as ia_expression  # noqa: F401

    return ia_expression
