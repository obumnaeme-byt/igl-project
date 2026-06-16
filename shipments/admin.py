"""
Shipments admin — enables Super Admin to view all shipments, senders,
receivers, and tracking events from the Django admin panel.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Shipment, Sender, Receiver, TrackingEvent


class SenderInline(admin.StackedInline):
    model = Sender
    extra = 0
    can_delete = False


class ReceiverInline(admin.StackedInline):
    model = Receiver
    extra = 0
    can_delete = False


class TrackingEventInline(admin.TabularInline):
    model = TrackingEvent
    extra = 0
    readonly_fields = ('status', 'location_description', 'notes', 'updated_by', 'event_timestamp')
    can_delete = False
    ordering = ('-event_timestamp',)


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display   = ('tracking_token', 'destination_country', 'current_status', 'payment_status', 'registered_by', 'created_at')
    list_filter    = ('current_status', 'payment_status', 'destination_country')
    search_fields  = ('tracking_token', 'sender__full_name', 'receiver__full_name', 'destination_country')
    readonly_fields = ('tracking_token', 'created_at', 'updated_at')
    ordering       = ('-created_at',)
    inlines        = [SenderInline, ReceiverInline, TrackingEventInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        (_('Tracking'), {'fields': ('tracking_token', 'current_status', 'current_location', 'estimated_delivery_at')}),
        (_('Package'), {'fields': ('package_description', 'weight_kg', 'quantity', 'declared_value', 'length_cm', 'width_cm', 'height_cm', 'service_reference')}),
        (_('Routing'), {'fields': ('destination_country', 'payment_status')}),
        (_('Audit'), {'fields': ('registered_by', 'created_at', 'updated_at')}),
    )


@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    list_display  = ('shipment', 'status', 'location_description', 'updated_by', 'event_timestamp')
    list_filter   = ('status',)
    search_fields = ('shipment__tracking_token', 'location_description')
    readonly_fields = ('event_timestamp',)
    ordering      = ('-event_timestamp',)
