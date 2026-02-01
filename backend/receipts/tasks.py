from celery import shared_task
from .ocr_engine import OcrPipeline
import os


@shared_task(bind=True)
def process_receipt_task(self, file_path):
    try:
        self.update_state(state='PROCESSING')

        pipeline = OcrPipeline(file_path)
        result = pipeline.run()

        if os.path.exists(file_path):
            os.remove(file_path)

        return result

    except Exception as e:
        print(f"Błąd OCR: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)
        raise e