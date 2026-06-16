"""
PDF Receipt Generator
=====================
Generates a branded A5/A4 receipt PDF using WeasyPrint.
Embeds a Code128 barcode (python-barcode) and QR code (qrcode) as base64.
Called from the portal view when admin clicks "Download Receipt".
"""
import io
import base64
import qrcode
from qrcode.constants import ERROR_CORRECT_M
from PIL import Image

try:
    import barcode
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone


def generate_barcode_b64(token: str) -> str:
    """
    Generates a Code128 barcode PNG from the tracking token.
    Returns a base64-encoded string suitable for embedding in HTML img src.
    Falls back to empty string if python-barcode is not installed.
    """
    if not BARCODE_AVAILABLE:
        return ''
    try:
        # Strip hyphens for barcode (Code128 handles alphanumeric fine)
        barcode_value = token.replace('-', '')
        code128 = barcode.get('code128', barcode_value, writer=ImageWriter())
        buffer = io.BytesIO()
        code128.write(buffer, options={
            'write_text': False,
            'module_height': 8.0,
            'quiet_zone': 2.0,
        })
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
    except Exception:
        return ''


def generate_qr_b64(token: str) -> str:
    """
    Generates a QR code PNG linking to the public tracking page.
    Returns base64-encoded string.
    """
    base_url = getattr(settings, 'SITE_BASE_URL', 'http://localhost:8000')
    tracking_url = f'{base_url}/track/{token}/'

    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_M,
        box_size=4,
        border=2,
    )
    qr.add_data(tracking_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def generate_receipt_pdf(shipment) -> bytes:
    """
    Builds the full receipt HTML and renders it to PDF via WeasyPrint.
    Returns raw PDF bytes that can be streamed as a FileResponse.

    Falls back to returning None if WeasyPrint is not available,
    so the view can serve the receipt as an HTML page instead.
    """
    barcode_b64 = generate_barcode_b64(shipment.tracking_token)
    qr_b64      = generate_qr_b64(shipment.tracking_token)

    payment_labels = {
        'unpaid':  ('Não pago', 'Unpaid', '#F59E0B'),
        'paid':    ('Pago', 'Paid', '#16A34A'),
        'partial': ('Parcialmente pago', 'Partially Paid', '#F97316'),
    }
    pt_label, en_label, badge_color = payment_labels.get(
        shipment.payment_status, ('Não pago', 'Unpaid', '#F59E0B')
    )

    context = {
        'shipment':           shipment,
        'sender':             getattr(shipment, 'sender', None),
        'receiver':           getattr(shipment, 'receiver', None),
        'barcode_b64':        barcode_b64,
        'qr_b64':             qr_b64,
        'created_date':       shipment.created_at.strftime('%d/%m/%Y'),
        'payment_label_pt':   pt_label,
        'payment_label_en':   en_label,
        'payment_badge_color': badge_color,
        'company_name':       settings.PDF_COMPANY_NAME,
        'company_address':    settings.PDF_COMPANY_ADDRESS,
        'company_phone':      settings.PDF_COMPANY_PHONE,
        'company_email':      settings.PDF_COMPANY_EMAIL,
        'base_url':           settings.SITE_BASE_URL,
    }

    html_string = render_to_string('receipts/shipment_receipt.html', context)

    if not WEASYPRINT_AVAILABLE:
        # Return HTML bytes as fallback — view will detect and serve as HTML
        return html_string.encode('utf-8')

    pdf_bytes = HTML(string=html_string, base_url=settings.SITE_BASE_URL).write_pdf()
    return pdf_bytes
