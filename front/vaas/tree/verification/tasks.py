"""
Celery tasks for heavy `ia` pipeline steps (non-blocking HTTP).

Imports use the same module paths as `ia/main.py` (`pipeline.*`) because
`vaas_project.settings` adds the `ia/` directory to `sys.path`.

REFACTOR NOTE:
--------------
If jobs need tenant-scoped temp directories, pass absolute paths derived from
`VerificationJob` / uploaded `FileField` storage — not hard-coded `ia/demo/...`.
"""
from celery import shared_task


@shared_task(bind=True, ack_late=True)
def pdf_to_images_task(self, pdf_paths: list[str], doctor_id: str, output_dir: str):
    """
    Wraps `ia.pipeline.pdf_to_images.pdf_to_images`.
    Runs in a worker process; keep arguments JSON-serializable for the broker.
    """
    from pipeline.pdf_to_images import pdf_to_images

    return pdf_to_images(pdf_paths, doctor_id, output_dir)


@shared_task(bind=True, ack_late=True)
def ocr_images_task(self, image_paths: list[str]):
    """
    Wraps `ia.pipeline.ocr.run_ocr`.
    """
    from pipeline.ocr import run_ocr

    return run_ocr(image_paths)
