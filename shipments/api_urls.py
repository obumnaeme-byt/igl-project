"""API URL routes for the public tracking endpoint and internal admin API."""
from django.urls import path
from . import api_views

urlpatterns = [
    # Public endpoint — no auth required
    path('track/<str:token>/', api_views.TrackingAPIView.as_view(), name='api_track'),

    # Admin-only endpoints
    path('portal/shipments/', api_views.ShipmentCreateAPIView.as_view(), name='api_shipment_create'),
    path('portal/shipments/<int:pk>/status/', api_views.ShipmentStatusUpdateAPIView.as_view(), name='api_shipment_status'),
]
