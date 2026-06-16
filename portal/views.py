"""
Admin Portal Views
==================
All views require the user to be logged in AND be a portal admin.
Uses a custom decorator `portal_login_required` rather than Django's
default which would redirect to /accounts/login/.

Views:
  - PortalLoginView       : /portal/login/
  - PortalLogoutView      : /portal/logout/
  - DashboardView         : /portal/dashboard/
  - ShipmentListView      : /portal/shipments/
  - ShipmentNewView       : /portal/shipments/new/
  - ShipmentDetailView    : /portal/shipments/<id>/
  - ShipmentStatusView    : /portal/shipments/<id>/update-status/
  - ShipmentReceiptView   : /portal/shipments/<id>/receipt/
  - ShipmentSuccessView   : /portal/shipments/<id>/success/
"""
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.paginator import Paginator
from axes.handlers.proxy import AxesProxyHandler

from shipments.models import Shipment, TrackingEvent
from shipments.forms import ShipmentForm, SenderForm, ReceiverForm, StatusUpdateForm
from shipments.receipt import generate_receipt_pdf


# ─── Custom Portal Auth Decorator ────────────────────────────────────────────

def portal_required(view_func):
    """
    Ensures the user is authenticated and has portal access.
    Redirects unauthenticated users to /portal/login/ (not /accounts/login/).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/portal/login/')
        if not (request.user.is_staff or request.user.is_superuser or
                getattr(request.user, 'is_portal_admin', False)):
            messages.error(request, _('You do not have access to the Admin Portal.'))
            return redirect('/portal/login/')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── Login / Logout ───────────────────────────────────────────────────────────

class PortalLoginView(View):
    template_name = 'portal/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('portal_dashboard')
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None and (user.is_staff or user.is_superuser or
                                  getattr(user, 'is_portal_admin', False)):
            login(request, user)
            next_url = request.GET.get('next', '/portal/dashboard/')
            return redirect(next_url)
        else:
            messages.error(request, _('Invalid username or password.'))
            return render(request, self.template_name, {'username': username})


class PortalLogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('portal_login')

    def get(self, request):
        logout(request)
        return redirect('portal_login')


# ─── Dashboard ────────────────────────────────────────────────────────────────

@method_decorator(portal_required, name='dispatch')
class DashboardView(View):
    template_name = 'portal/dashboard.html'

    def get(self, request):
        qs = Shipment.objects.all()
        total_shipments  = qs.count()
        in_transit_count = qs.filter(current_status__in=['in_transit', 'picked_up', 'customs', 'out_for_delivery']).count()
        delivered_count  = qs.filter(current_status='delivered').count()
        recent_shipments = qs.select_related('sender', 'receiver')[:8]

        # Status breakdown for mini chart
        status_counts = {s[0]: 0 for s in Shipment.Status.choices}
        for row in qs.values('current_status').annotate(c=Count('id')):
            status_counts[row['current_status']] = row['c']

        context = {
            'total_shipments':  total_shipments,
            'in_transit_count': in_transit_count,
            'delivered_count':  delivered_count,
            'recent_shipments': recent_shipments,
            'status_counts':    status_counts,
        }
        return render(request, self.template_name, context)


# ─── Shipment List ────────────────────────────────────────────────────────────

@method_decorator(portal_required, name='dispatch')
class ShipmentListView(View):
    template_name = 'portal/shipment_list.html'
    PAGE_SIZE = 25

    def get(self, request):
        qs = Shipment.objects.select_related('sender', 'receiver').order_by('-created_at')

        # Search
        q = request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(tracking_token__icontains=q) |
                Q(sender__full_name__icontains=q) |
                Q(receiver__full_name__icontains=q) |
                Q(destination_country__icontains=q)
            )

        # Filters
        status_filter = request.GET.get('status', '')
        if status_filter:
            qs = qs.filter(current_status=status_filter)

        date_from = request.GET.get('date_from', '')
        date_to   = request.GET.get('date_to', '')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        paginator = Paginator(qs, self.PAGE_SIZE)
        page_obj  = paginator.get_page(request.GET.get('page'))

        context = {
            'page_obj':      page_obj,
            'q':             q,
            'status_filter': status_filter,
            'date_from':     date_from,
            'date_to':       date_to,
            'status_choices': Shipment.Status.choices,
        }
        return render(request, self.template_name, context)


# ─── New Shipment ─────────────────────────────────────────────────────────────

@method_decorator(portal_required, name='dispatch')
class ShipmentNewView(View):
    template_name = 'portal/shipment_form.html'

    def get(self, request):
        return render(request, self.template_name, {
            'shipment_form': ShipmentForm(),
            'sender_form':   SenderForm(),
            'receiver_form': ReceiverForm(),
        })

    def post(self, request):
        shipment_form = ShipmentForm(request.POST)
        sender_form   = SenderForm(request.POST)
        receiver_form = ReceiverForm(request.POST)

        if all([shipment_form.is_valid(), sender_form.is_valid(), receiver_form.is_valid()]):
            shipment = shipment_form.save(commit=False)
            shipment.registered_by = request.user
            shipment.save()

            sender = sender_form.save(commit=False)
            sender.shipment = shipment
            sender.save()

            receiver = receiver_form.save(commit=False)
            receiver.shipment = shipment
            receiver.save()

            # Create the initial "Registered" tracking event
            TrackingEvent.objects.create(
                shipment=shipment,
                status=Shipment.Status.REGISTERED,
                location_description=sender.city,
                notes=_('Shipment registered.'),
                updated_by=request.user,
                event_timestamp=timezone.now(),
            )

            return redirect('portal_shipment_success', pk=shipment.pk)

        return render(request, self.template_name, {
            'shipment_form': shipment_form,
            'sender_form':   sender_form,
            'receiver_form': receiver_form,
        })


# ─── Shipment Detail ──────────────────────────────────────────────────────────

@method_decorator(portal_required, name='dispatch')
class ShipmentDetailView(View):
    template_name = 'portal/shipment_detail.html'

    def get(self, request, pk):
        shipment = get_object_or_404(
            Shipment.objects.select_related('sender', 'receiver'),
            pk=pk,
        )
        events = shipment.tracking_events.select_related('updated_by').order_by('event_timestamp')
        status_form = StatusUpdateForm(instance=shipment)
        return render(request, self.template_name, {
            'shipment':    shipment,
            'events':      events,
            'status_form': status_form,
        })


# ─── Status Update ────────────────────────────────────────────────────────────

@method_decorator(portal_required, name='dispatch')
class ShipmentStatusView(View):
    def post(self, request, pk):
        shipment    = get_object_or_404(Shipment, pk=pk)
        status_form = StatusUpdateForm(request.POST, instance=shipment)
        notes       = request.POST.get('notes', '').strip()

        if status_form.is_valid():
            old_status = shipment.current_status
            updated    = status_form.save()

            TrackingEvent.objects.create(
                shipment=updated,
                status=updated.current_status,
                location_description=updated.current_location or '',
                notes=notes,
                updated_by=request.user,
                event_timestamp=timezone.now(),
            )
            messages.success(request, _('Status updated successfully.'))
        else:
            messages.error(request, _('Please correct the errors below.'))

        return redirect('portal_shipment_detail', pk=pk)


# ─── Receipt Download ─────────────────────────────────────────────────────────

@method_decorator(portal_required, name='dispatch')
class ShipmentReceiptView(View):
    def get(self, request, pk):
        shipment = get_object_or_404(
            Shipment.objects.select_related('sender', 'receiver'),
            pk=pk,
        )
        pdf_bytes = generate_receipt_pdf(shipment)
        filename  = f'IGL-{shipment.tracking_token}-receipt.pdf'

        # Detect if WeasyPrint returned HTML fallback (starts with <!DOCTYPE)
        if pdf_bytes[:9] == b'<!DOCTYPE':
            return HttpResponse(pdf_bytes, content_type='text/html')

        response = FileResponse(
            iter([pdf_bytes]),
            content_type='application/pdf',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# ─── Success Page ─────────────────────────────────────────────────────────────

@method_decorator(portal_required, name='dispatch')
class ShipmentSuccessView(View):
    template_name = 'portal/shipment_success.html'

    def get(self, request, pk):
        shipment = get_object_or_404(
            Shipment.objects.select_related('sender', 'receiver'),
            pk=pk,
        )
        return render(request, self.template_name, {'shipment': shipment})
