"""
shipments/utils.py
==================
Utility functions for:
  - Generating Code128 barcodes (python-barcode + Pillow)
  - Generating QR codes (qrcode library)
  - Rendering PDF receipts (WeasyPrint HTML → PDF)

All image data is returned as base64-encoded strings for embedding
directly in HTML/PDF templates without filesystem I/O.
"""

import io
import base64
import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def generate_barcode_b64(token: str) -> str:
    """
    Generate a Code128 barcode for the given token string.
    Returns a base64-encoded PNG string suitable for <img src="data:image/png;base64,...">
    """
    try:
        import barcode
        from barcode.writer import ImageWriter

        code128 = barcode.get('code128', token, writer=ImageWriter())
        buffer = io.BytesIO()
        code128.write(buffer, options={
            'module_width': 0.8,
            'module_height': 8.0,
            'quiet_zone': 2.5,
            'font_size': 6,
            'text_distance': 2.0,
            'background': 'white',
            'foreground': 'black',
            'write_text': True,
        })
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
    except ImportError:
        logger.warning("python-barcode not installed; barcode will be empty.")
        return ''
    except Exception as exc:
        logger.error(f"Barcode generation failed: {exc}")
        return ''


def generate_qr_b64(url: str) -> str:
    """
    Generate a QR code PNG for the given URL.
    Returns a base64-encoded PNG string.
    Error correction: Level M (15% recovery).
    """
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_M

        qr = qrcode.QRCode(
            version=1,
            error_correction=ERROR_CORRECT_M,
            box_size=4,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
    except ImportError:
        logger.warning("qrcode not installed; QR code will be empty.")
        return ''
    except Exception as exc:
        logger.error(f"QR code generation failed: {exc}")
        return ''


def generate_receipt_pdf(shipment) -> bytes:
    """
    Render the shipment receipt HTML template and convert to PDF bytes
    using WeasyPrint.

    Args:
        shipment: Shipment model instance (with sender/receiver related objects loaded)

    Returns:
        bytes: PDF binary content ready to serve as FileResponse
    """
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        raise RuntimeError("WeasyPrint is not installed. Run: pip install weasyprint")

    tracking_url = shipment.get_tracking_url()
    barcode_b64 = generate_barcode_b64(shipment.tracking_token)
    qr_b64 = generate_qr_b64(tracking_url)

    payment_labels = {
        'unpaid': 'Não pago',
        'paid': 'Pago',
        'partial': 'Parcialmente pago',
    }

    context = {
        'shipment': shipment,
        'sender': shipment.sender,
        'receiver': shipment.receiver,
        'barcode_b64': barcode_b64,
        'qr_b64': qr_b64,
        'tracking_url': tracking_url,
        'created_date': shipment.created_at.strftime('%d/%m/%Y'),
        'payment_status_label': payment_labels.get(shipment.payment_status, 'Não pago'),
        'company_name': settings.PDF_COMPANY_NAME,
        'company_address': settings.PDF_COMPANY_ADDRESS,
        'company_phone': settings.PDF_COMPANY_PHONE,
        'company_email': settings.PDF_COMPANY_EMAIL,
    }

    html_string = render_to_string('receipts/shipment_receipt.html', context)

    pdf_bytes = HTML(string=html_string, base_url=settings.SITE_URL).write_pdf()
    return pdf_bytes
