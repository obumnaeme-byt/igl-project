"""
Shipments Models
================
Core data models for the IGL platform:
  - Shipment       : the main package record with tracking token
  - Sender         : sender contact/address info (OneToOne with Shipment)
  - Receiver       : receiver contact/address info (OneToOne with Shipment)
  - TrackingEvent  : immutable history log of every status change
"""
import random
import string
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


def generate_tracking_token():
    """
    Generates a unique token in format IGL-XXXX-XXXX.
    Uses uppercase letters + digits. Performs collision checking.
    Falls back with up to 3 retries before raising an error.
    """
    chars = string.ascii_uppercase + string.digits
    for attempt in range(3):
        part1 = ''.join(random.choices(chars, k=4))
        part2 = ''.join(random.choices(chars, k=4))
        token = f'IGL-{part1}-{part2}'
        if not Shipment.objects.filter(tracking_token=token).exists():
            return token
    raise ValueError("Failed to generate a unique tracking token after 3 attempts.")


class Shipment(models.Model):
    """
    Central shipment record created when admin registers a new package.
    Owns the tracking token that customers use to look up their delivery.
    """
    class Status(models.TextChoices):
        REGISTERED    = 'registered',      _('Registered')
        PICKED_UP     = 'picked_up',       _('Picked Up')
        IN_TRANSIT    = 'in_transit',      _('In Transit')
        CUSTOMS       = 'customs',         _('Customs Clearance')
        OUT_DELIVERY  = 'out_for_delivery', _('Out for Delivery')
        DELIVERED     = 'delivered',       _('Delivered')
        FAILED        = 'failed_delivery', _('Failed Delivery')
        RETURNED      = 'returned',        _('Returned to Sender')
        ON_HOLD       = 'on_hold',         _('On Hold')

    class PaymentStatus(models.TextChoices):
        UNPAID   = 'unpaid',   _('Unpaid')
        PAID     = 'paid',     _('Paid')
        PARTIAL  = 'partial',  _('Partially Paid')

    # ── Identification ────────────────────────────────────────────────────────
    tracking_token = models.CharField(
        max_length=16,
        unique=True,
        default=generate_tracking_token,
        editable=False,
        verbose_name=_('Tracking Token'),
        db_index=True,
    )

    # ── Package details ───────────────────────────────────────────────────────
    package_description = models.TextField(verbose_name=_('Package Description'))
    weight_kg           = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name=_('Weight (kg)'))
    quantity            = models.PositiveIntegerField(default=1, verbose_name=_('Quantity'))
    declared_value      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_('Declared Value'))
    length_cm           = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, verbose_name=_('Length (cm)'))
    width_cm            = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, verbose_name=_('Width (cm)'))
    height_cm           = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, verbose_name=_('Height (cm)'))
    service_reference   = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('Service Reference'))

    # ── Routing ───────────────────────────────────────────────────────────────
    destination_country = models.CharField(max_length=100, verbose_name=_('Destination Country'))

    # ── Status & location ─────────────────────────────────────────────────────
    current_status   = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.REGISTERED,
        verbose_name=_('Current Status'),
        db_index=True,
    )
    current_location = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('Current Location'))
    payment_status   = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        verbose_name=_('Payment Status'),
    )

    # ── Dates ─────────────────────────────────────────────────────────────────
    estimated_delivery_at = models.DateTimeField(verbose_name=_('Estimated Delivery'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Registered At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Last Updated'))

    # ── Staff ─────────────────────────────────────────────────────────────────
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_shipments',
        verbose_name=_('Registered By'),
    )

    class Meta:
        verbose_name = _('Shipment')
        verbose_name_plural = _('Shipments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tracking_token']),
            models.Index(fields=['current_status']),
            models.Index(fields=['destination_country']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        return f'{self.tracking_token} → {self.destination_country}'

    @property
    def status_badge_class(self):
        """Returns CSS class for status badge colouring in templates."""
        mapping = {
            'registered':      'badge-secondary',
            'picked_up':       'badge-info',
            'in_transit':      'badge-warning',
            'customs':         'badge-warning',
            'out_for_delivery':'badge-primary',
            'delivered':       'badge-success',
            'failed_delivery': 'badge-danger',
            'returned':        'badge-dark',
            'on_hold':         'badge-light text-dark',
        }
        return mapping.get(self.current_status, 'badge-secondary')

    @property
    def payment_badge_class(self):
        mapping = {
            'unpaid':  'badge-amber',
            'paid':    'badge-success',
            'partial': 'badge-orange',
        }
        return mapping.get(self.payment_status, 'badge-secondary')


class ContactInfo(models.Model):
    """
    Abstract base for Sender and Receiver — both share identical fields.
    """
    full_name     = models.CharField(max_length=200, verbose_name=_('Full Name'))
    phone_number  = models.CharField(max_length=20, verbose_name=_('Phone Number'))
    address_line1 = models.CharField(max_length=255, verbose_name=_('Address Line 1'))
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name=_('Address Line 2'))
    city          = models.CharField(max_length=100, verbose_name=_('City'))
    state_province = models.CharField(max_length=100, blank=True, verbose_name=_('State / Province'))
    country       = models.CharField(max_length=100, verbose_name=_('Country'))
    postal_code   = models.CharField(max_length=20, blank=True, verbose_name=_('Postal Code'))

    class Meta:
        abstract = True

    def masked_phone(self):
        """Returns phone with all but last 3 digits masked."""
        if len(self.phone_number) > 3:
            return '*' * (len(self.phone_number) - 3) + self.phone_number[-3:]
        return self.phone_number


class Sender(ContactInfo):
    """Sender (Remetente) linked one-to-one with a Shipment."""
    shipment = models.OneToOneField(
        Shipment,
        on_delete=models.CASCADE,
        related_name='sender',
        verbose_name=_('Shipment'),
    )

    class Meta:
        verbose_name = _('Sender')
        verbose_name_plural = _('Senders')

    def __str__(self):
        return f'Sender: {self.full_name} [{self.shipment.tracking_token}]'


class Receiver(ContactInfo):
    """Receiver (Destinatário) linked one-to-one with a Shipment."""
    shipment = models.OneToOneField(
        Shipment,
        on_delete=models.CASCADE,
        related_name='receiver',
        verbose_name=_('Shipment'),
    )

    class Meta:
        verbose_name = _('Receiver')
        verbose_name_plural = _('Receivers')

    def __str__(self):
        return f'Receiver: {self.full_name} [{self.shipment.tracking_token}]'


class TrackingEvent(models.Model):
    """
    Immutable audit log of every status change.
    Each entry records who changed it, when, to what status, and from where.
    Customers see this as the delivery timeline on the tracking page.
    """
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='tracking_events',
        verbose_name=_('Shipment'),
    )
    status = models.CharField(
        max_length=30,
        choices=Shipment.Status.choices,
        verbose_name=_('Status'),
    )
    location_description = models.CharField(max_length=255, blank=True, verbose_name=_('Location'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Updated By'),
    )
    event_timestamp = models.DateTimeField(default=timezone.now, verbose_name=_('Timestamp'))

    class Meta:
        verbose_name = _('Tracking Event')
        verbose_name_plural = _('Tracking Events')
        ordering = ['-event_timestamp']
        indexes = [
            models.Index(fields=['shipment', '-event_timestamp']),
        ]

    def __str__(self):
        return f'{self.shipment.tracking_token} — {self.get_status_display()} @ {self.event_timestamp:%Y-%m-%d %H:%M}'
