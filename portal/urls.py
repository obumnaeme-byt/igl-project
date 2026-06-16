"""Admin Portal URL patterns — all under /portal/ prefix."""
from django.urls import path
from . import views

urlpatterns = [
    path('login/',                           views.PortalLoginView.as_view(),      name='portal_login'),
    path('logout/',                          views.PortalLogoutView.as_view(),     name='portal_logout'),
    path('dashboard/',                       views.DashboardView.as_view(),        name='portal_dashboard'),
    path('shipments/',                       views.ShipmentListView.as_view(),     name='portal_shipment_list'),
    path('shipments/new/',                   views.ShipmentNewView.as_view(),      name='portal_shipment_new'),
    path('shipments/<int:pk>/',              views.ShipmentDetailView.as_view(),   name='portal_shipment_detail'),
    path('shipments/<int:pk>/update-status/',views.ShipmentStatusView.as_view(),  name='portal_shipment_status'),
    path('shipments/<int:pk>/receipt/',      views.ShipmentReceiptView.as_view(),  name='portal_shipment_receipt'),
    path('shipments/<int:pk>/success/',      views.ShipmentSuccessView.as_view(),  name='portal_shipment_success'),
]
