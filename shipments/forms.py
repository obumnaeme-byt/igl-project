"""
Shipment Registration Forms
============================
All forms used in the Admin Portal for creating and updating shipments.
Cleaned data is validated server-side regardless of any client-side checks.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Shipment, Sender, Receiver


class SenderForm(forms.ModelForm):
    class Meta:
        model = Sender
        exclude = ['shipment']
        widgets = {
            'full_name':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Full Name')}),
            'phone_number':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('+1234567890')}),
            'address_line1':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Street address')}),
            'address_line2':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Apt, suite, etc. (optional)')}),
            'city':           forms.TextInput(attrs={'class': 'form-control'}),
            'state_province': forms.TextInput(attrs={'class': 'form-control'}),
            'country':        forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code':    forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError(_('Name must be at least 2 characters.'))
        return name

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 7:
            raise forms.ValidationError(_('Enter a valid phone number (minimum 7 digits).'))
        return phone


class ReceiverForm(forms.ModelForm):
    class Meta:
        model = Receiver
        exclude = ['shipment']
        widgets = {
            'full_name':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Full Name')}),
            'phone_number':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('+1234567890')}),
            'address_line1':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Street address')}),
            'address_line2':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Apt, suite, etc. (optional)')}),
            'city':           forms.TextInput(attrs={'class': 'form-control'}),
            'state_province': forms.TextInput(attrs={'class': 'form-control'}),
            'country':        forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code':    forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError(_('Name must be at least 2 characters.'))
        return name

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 7:
            raise forms.ValidationError(_('Enter a valid phone number (minimum 7 digits).'))
        return phone


class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = [
            'package_description', 'weight_kg', 'quantity',
            'declared_value', 'length_cm', 'width_cm', 'height_cm',
            'service_reference', 'destination_country',
            'estimated_delivery_at', 'payment_status',
        ]
        widgets = {
            'package_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'weight_kg':           forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'quantity':            forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'declared_value':      forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'length_cm':           forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'width_cm':            forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'height_cm':           forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'service_reference':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g. Express, Standard, Two-day')}),
            'destination_country': forms.TextInput(attrs={'class': 'form-control'}),
            'estimated_delivery_at': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure datetime widget renders correctly in HTML5 input
        if self.instance and self.instance.pk and self.instance.estimated_delivery_at:
            self.initial['estimated_delivery_at'] = self.instance.estimated_delivery_at.strftime('%Y-%m-%dT%H:%M')

    def clean_estimated_delivery_at(self):
        dt = self.cleaned_data.get('estimated_delivery_at')
        if dt and dt < timezone.now():
            raise forms.ValidationError(_('Estimated delivery date must be in the future.'))
        return dt


class StatusUpdateForm(forms.ModelForm):
    """
    Lightweight form for admins to update status and location on a shipment.
    Also creates a new TrackingEvent entry automatically in the view.
    """
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': _('Optional notes for this update')}),
        label=_('Notes'),
    )

    class Meta:
        model = Shipment
        fields = ['current_status', 'current_location', 'payment_status']
        widgets = {
            'current_status':   forms.Select(attrs={'class': 'form-select'}),
            'current_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g. Lagos Airport Hub, Nigeria')}),
            'payment_status':   forms.Select(attrs={'class': 'form-select'}),
        }
