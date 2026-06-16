"""
core/api_views.py
=================
DRF API Views:
  - TrackShipmentAPIView      : GET /api/v1/track/{token}/ — public, rate-limited
  - CreateShipmentAPIView     : POST /api/v1/portal/shipments/ — admin auth
  - UpdateShipmentStatusAPIView: PATCH /api/v1/portal/shipments/{id}/status/ — admin auth
"""

import logging

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from shipments.models import Shipment, TrackingEvent, ShipmentStatus
from shipments.serializers import (
    PublicShipmentSerializer,
    CreateShipmentSerializer,
    UpdateStatusSerializer,
)

logger = logging.getLogger(__name__)


class TrackShipmentAPIView(APIView):
    """
    GET /api/v1/track/{token}/
    Public endpoint. Rate-limited to 30/min per IP via DRF throttling.
    """
    permission_classes = [AllowAny]
    throttle_scope = 'anon'

    def get(self, request, token):
        token = token.strip().upper()

        try:
            shipment = Shipment.objects.select_related(
                'receiver'
            ).prefetch_related('events').get(tracking_token=token)
        except Shipment.DoesNotExist:
            return Response(
                {'error': 'shipment_not_found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PublicShipmentSerializer(shipment)
        return Response(serializer.data)


class CreateShipmentAPIView(APIView):
    """
    POST /api/v1/portal/shipments/
    Admin-only. Creates shipment + sender + receiver + initial tracking event.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateShipmentSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            shipment = serializer.save()
            return Response({
                'tracking_token': shipment.tracking_token,
                'receipt_url': f'/portal/shipments/{shipment.pk}/receipt/',
                'shipment_id': shipment.pk,
            }, status=status.HTTP_201_CREATED)

        return Response({'errors': serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class UpdateShipmentStatusAPIView(APIView):
    """
    PATCH /api/v1/portal/shipments/{id}/status/
    Admin-only. Appends a TrackingEvent and updates current status.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)

        try:
            shipment = Shipment.objects.get(pk=pk)
        except Shipment.DoesNotExist:
            return Response({'error': 'not_found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateStatusSerializer(data=request.data)
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            location = serializer.validated_data.get('location_description', '')
            notes = serializer.validated_data.get('notes', '')

            with transaction.atomic():
                TrackingEvent.objects.create(
                    shipment=shipment,
                    status=new_status,
                    location_description=location,
                    notes=notes,
                    updated_by=request.user,
                )
                shipment.current_status = new_status
                if location:
                    shipment.current_location = location
                shipment.save(update_fields=['current_status', 'current_location', 'updated_at'])

            return Response({
                'shipment_id': pk,
                'new_status': new_status,
                'updated_at': shipment.updated_at.isoformat(),
            })

        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
