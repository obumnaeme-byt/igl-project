"""
Celery async tasks.
PDF generation is offloaded here to avoid blocking the HTTP response.
"""
from celery import shared_task


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def generate_receipt_async(self, shipment_id: int):
    """
    Async task: generate PDF receipt for a shipment and store it in media/.
    Retries up to 3 times on failure.
    """
    try:
        from .models import Shipment
        from .receipt import generate_receipt_pdf
        import os
        from django.conf import settings

        shipment = Shipment.objects.select_related('sender', 'receiver').get(pk=shipment_id)
        pdf_bytes = generate_receipt_pdf(shipment)

        receipts_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
        os.makedirs(receipts_dir, exist_ok=True)

        filename = f'IGL-{shipment.tracking_token}-receipt.pdf'
        filepath = os.path.join(receipts_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(pdf_bytes)

        return {'status': 'ok', 'path': filepath}
    except Exception as exc:
        raise self.retry(exc=exc)
