"""
portal/forms.py
===============
Django Forms for the Admin Portal:
  - AdminLoginForm      : Secure login with username + password
  - ShipmentForm        : Register a new shipment (package details only)
  - SenderForm          : Sender information
  - ReceiverForm        : Receiver information
  - TrackingUpdateForm  : Update shipment status + location
"""

import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from shipments.models import (
    Shipment, Sender, Receiver, TrackingEvent,
    ShipmentStatus, PaymentStatus,
)


# ─── Login Form ───────────────────────────────────────────────────────────────

class AdminLoginForm(AuthenticationForm):
    """
    Extends Django's AuthenticationForm.
    Adds Bootstrap-compatible widget classes and custom error messages.
    """
    username = forms.CharField(
        label=_('Username'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter your username'),
            'autofocus': True,
            'autocomplete': 'username',
        }),
    )
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter your password'),
            'autocomplete': 'current-password',
        }),
    )

    error_messages = {
        'invalid_login': _(
            'Invalid username or password. '
            'Please check your credentials and try again.'
        ),
        'inactive': _('This account has been deactivated.'),
    }


# ─── Shipment Registration Forms ─────────────────────────────────────────────

INPUT_CLASS = 'form-input'
SELECT_CLASS = 'form-select'


class SenderForm(forms.ModelForm):
    class Meta:
        model = Sender
        exclude = ('shipment',)
        widgets = {
            'full_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('Full name')}),
            'phone_number': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('+1 234 567 8900')}),
            'address_line1': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('Street address')}),
            'address_line2': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('Apt, suite, etc. (optional)')}),
            'city': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('City')}),
            'state_province': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('State / Province')}),
            'country': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('Country')}),
            'postal_code': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('Postal code')}),
        }

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError(_('Name must be at least 2 characters.'))
        return name

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        # Allow +, digits, spaces, dashes, parentheses; minimum 7 digits
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 7:
            raise forms.ValidationError(_('Enter a valid phone number (minimum 7 digits).'))
        return phone


class ReceiverForm(forms.ModelForm):
    class Meta:
        model = Receiver
        exclude = ('shipment',)
        widgets = {
            'full_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('Full name')}),
            'phone_number': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('+1 234 567 8900')}),
            'address_line1': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('Street address')}),
            'address_line2': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('Apt, complement (optional)')}),
            'city': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('City')}),
            'state_province': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('State / Province')}),
            'country': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('Country')}),
            'postal_code': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': _('CEP / Postal code')}),
        }

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError(_('Name must be at least 2 characters.'))
        return name

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 7:
            raise forms.ValidationError(_('Enter a valid phone number (minimum 7 digits).'))
        return phone


class ShipmentForm(forms.ModelForm):
    """Package details section of the shipment registration form."""

    class Meta:
        model = Shipment
        fields = (
            'package_description',
            'weight_kg',
            'quantity',
            'declared_value',
            'length_cm',
            'width_cm',
            'height_cm',
            'service_reference',
            'payment_status',
            'destination_country',
            'estimated_delivery_at',
        )
        widgets = {
            'package_description': forms.Textarea(attrs={
                'class': INPUT_CLASS, 'rows': 3,
                'placeholder': _('Describe the package contents'),
            }),
            'weight_kg': forms.NumberInput(attrs={
                'class': INPUT_CLASS, 'step': '0.01',
                'placeholder': _('e.g. 2.5'),
            }),
            'quantity': forms.NumberInput(attrs={
                'class': INPUT_CLASS, 'min': '1', 'value': '1',
            }),
            'declared_value': forms.NumberInput(attrs={
                'class': INPUT_CLASS, 'step': '0.01',
                'placeholder': _('e.g. 150.00'),
            }),
            'length_cm': forms.NumberInput(attrs={
                'class': INPUT_CLASS, 'step': '0.1',
                'placeholder': _('Length (cm)'),
            }),
            'width_cm': forms.NumberInput(attrs={
                'class': INPUT_CLASS, 'step': '0.1',
                'placeholder': _('Width (cm)'),
            }),
            'height_cm': forms.NumberInput(attrs={
                'class': INPUT_CLASS, 'step': '0.1',
                'placeholder': _('Height (cm)'),
            }),
            'service_reference': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': _('e.g. Express, Standard, Dois dias'),
            }),
            'payment_status': forms.Select(attrs={'class': SELECT_CLASS}),
            'destination_country': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': _('e.g. Nigeria, Brazil, Germany'),
            }),
            'estimated_delivery_at': forms.DateTimeInput(
                attrs={'class': INPUT_CLASS, 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estimated_delivery_at'].input_formats = ['%Y-%m-%dT%H:%M']

    def clean_estimated_delivery_at(self):
        dt = self.cleaned_data.get('estimated_delivery_at')
        if dt and dt <= timezone.now():
            raise forms.ValidationError(_('Estimated delivery must be a future date and time.'))
        return dt


# ─── Status Update Form ───────────────────────────────────────────────────────

class TrackingUpdateForm(forms.Form):
    """
    Used on the shipment detail page to add a new TrackingEvent.
    Does NOT directly update the model — the view handles that atomically.
    """
    status = forms.ChoiceField(
        label=_('New Status'),
        choices=ShipmentStatus.choices,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
    )
    location_description = forms.CharField(
        label=_('Current Location'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': _('e.g. Lagos Island Hub, Nigeria'),
        }),
    )
    notes = forms.CharField(
        label=_('Notes (optional)'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': INPUT_CLASS,
            'rows': 2,
            'placeholder': _('Any additional information for this update'),
        }),
    )

    def clean_status(self):
        status = self.cleaned_data.get('status')
        if not status:
            raise forms.ValidationError(_('Status is required.'))
        return status


# ─── Payment Status Update Form ───────────────────────────────────────────────

class PaymentStatusForm(forms.Form):
    payment_status = forms.ChoiceField(
        label=_('Payment Status'),
        choices=PaymentStatus.choices,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
    )
