"""
REST API Views
==============
GET  /api/v1/track/{token}/         — public, rate-limited, no auth
POST /api/v1/portal/shipments/      — admin auth required
PATCH /api/v1/portal/shipments/{id}/status/ — admin auth required
"""
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.throttling import AnonRateThrottle
from django.utils import timezone
from .models import Shipment, TrackingEvent
from .serializers import (
    ShipmentTrackingSerializer,
    ShipmentCreateSerializer,
)


class TrackingRateThrottle(AnonRateThrottle):
    rate = '30/min'


class TrackingAPIView(APIView):
    """
    Public tracking endpoint. Accepts a token, returns shipment status + timeline.
    Rate-limited to 30 requests/minute per IP address.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [TrackingRateThrottle]

    TOKEN_PATTERN = re.compile(r'^IGL-[A-Z0-9]{4}-[A-Z0-9]{4}$')

    def get(self, request, token):
        token = token.upper()
        if not self.TOKEN_PATTERN.match(token):
            return Response({'error': 'invalid_token_format'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            shipment = (
                Shipment.objects
                .select_related('receiver')
                .prefetch_related('tracking_events')
                .get(tracking_token=token)
            )
        except Shipment.DoesNotExist:
            return Response({'error': 'shipment_not_found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ShipmentTrackingSerializer(shipment)
        return Response(serializer.data)


class ShipmentCreateAPIView(APIView):
    """Create a shipment via API (for future mobile admin app)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ShipmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            shipment = serializer.save(registered_by=request.user)
            # Auto-create first tracking event
            TrackingEvent.objects.create(
                shipment=shipment,
                status=Shipment.Status.REGISTERED,
                location_description=request.data.get('sender', {}).get('city', ''),
                updated_by=request.user,
            )
            return Response({
                'tracking_token': shipment.tracking_token,
                'receipt_url': f'/portal/shipments/{shipment.pk}/receipt/',
                'shipment_id': shipment.pk,
            }, status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class ShipmentStatusUpdateAPIView(APIView):
    """Update shipment status + location; creates a TrackingEvent."""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            shipment = Shipment.objects.get(pk=pk)
        except Shipment.DoesNotExist:
            return Response({'error': 'not_found'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        location   = request.data.get('location_description', '')
        notes      = request.data.get('notes', '')

        valid_statuses = [s[0] for s in Shipment.Status.choices]
        if new_status not in valid_statuses:
            return Response({'error': 'invalid_status'}, status=status.HTTP_400_BAD_REQUEST)

        shipment.current_status   = new_status
        shipment.current_location = location
        shipment.save(update_fields=['current_status', 'current_location', 'updated_at'])

        TrackingEvent.objects.create(
            shipment=shipment,
            status=new_status,
            location_description=location,
            notes=notes,
            updated_by=request.user,
            event_timestamp=timezone.now(),
        )

        return Response({
            'shipment_id': shipment.pk,
            'new_status': new_status,
            'updated_at': shipment.updated_at,
        })
