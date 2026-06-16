"""
core/api_urls.py
================
DRF REST API URL patterns.
Mounted at /api/v1/ in the root urls.py.
"""

from django.urls import path
from .api_views import TrackShipmentAPIView, CreateShipmentAPIView, UpdateShipmentStatusAPIView

urlpatterns = [
    # Public: no authentication
    path('track/<str:token>/', TrackShipmentAPIView.as_view(), name='api_track'),

    # Internal: admin authentication required
    path('portal/shipments/',                    CreateShipmentAPIView.as_view(),       name='api_create_shipment'),
    path('portal/shipments/<int:pk>/status/',    UpdateShipmentStatusAPIView.as_view(), name='api_update_status'),
]
