"""
DRF Serializers for the public tracking API endpoint.
Sensitive data (full phone, full address) is masked before serialization.
"""
from rest_framework import serializers
from .models import Shipment, TrackingEvent


class TrackingEventSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TrackingEvent
        fields = ['status', 'status_display', 'location_description', 'notes', 'event_timestamp']


class PublicReceiverSerializer(serializers.Serializer):
    """Only exposes city and masked name — never full address or phone."""
    full_name = serializers.SerializerMethodField()
    city      = serializers.CharField()

    def get_full_name(self, obj):
        parts = obj.full_name.split()
        if len(parts) >= 2:
            return f'{parts[0][0]}***  {parts[-1][0]}***'
        return f'{obj.full_name[0]}***'


class ShipmentTrackingSerializer(serializers.ModelSerializer):
    """
    Public-safe serializer. Used by GET /api/v1/track/{token}/.
    Phone numbers and full addresses are NEVER exposed here.
    """
    receiver       = PublicReceiverSerializer(read_only=True)
    timeline       = TrackingEventSerializer(source='tracking_events', many=True, read_only=True)
    status_display = serializers.CharField(source='get_current_status_display', read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'tracking_token', 'current_status', 'status_display',
            'current_location', 'estimated_delivery_at',
            'destination_country', 'receiver', 'timeline',
        ]


class ShipmentCreateSerializer(serializers.ModelSerializer):
    """Used by POST /api/v1/portal/shipments/ (admin API)."""
    sender_full_name     = serializers.CharField(write_only=True)
    sender_phone         = serializers.CharField(write_only=True)
    sender_address       = serializers.CharField(write_only=True)
    sender_city          = serializers.CharField(write_only=True)
    sender_country       = serializers.CharField(write_only=True)
    receiver_full_name   = serializers.CharField(write_only=True)
    receiver_phone       = serializers.CharField(write_only=True)
    receiver_address     = serializers.CharField(write_only=True)
    receiver_city        = serializers.CharField(write_only=True)
    receiver_country     = serializers.CharField(write_only=True)
    tracking_token       = serializers.CharField(read_only=True)
    receipt_url          = serializers.SerializerMethodField()

    class Meta:
        model = Shipment
        fields = [
            'tracking_token', 'receipt_url',
            'package_description', 'weight_kg', 'estimated_delivery_at',
            'sender_full_name', 'sender_phone', 'sender_address', 'sender_city', 'sender_country',
            'receiver_full_name', 'receiver_phone', 'receiver_address', 'receiver_city', 'receiver_country',
        ]

    def get_receipt_url(self, obj):
        return f'/portal/shipments/{obj.pk}/receipt/'

    def create(self, validated_data):
        from .models import Sender, Receiver
        sender_data = {
            'full_name':     validated_data.pop('sender_full_name'),
            'phone_number':  validated_data.pop('sender_phone'),
            'address_line1': validated_data.pop('sender_address'),
            'city':          validated_data.pop('sender_city'),
            'country':       validated_data.pop('sender_country'),
        }
        receiver_data = {
            'full_name':     validated_data.pop('receiver_full_name'),
            'phone_number':  validated_data.pop('receiver_phone'),
            'address_line1': validated_data.pop('receiver_address'),
            'city':          validated_data.pop('receiver_city'),
            'country':       validated_data.pop('receiver_country'),
        }
        shipment = Shipment.objects.create(**validated_data)
        Sender.objects.create(shipment=shipment, **sender_data)
        Receiver.objects.create(shipment=shipment, **receiver_data)
        return shipment
