"""
Core Views — Public-facing pages
==================================
No login required for any of these views.
- HomeView     : homepage with tracking token input
- TrackView    : shipment tracking result page
- AboutView    : about page
- ServicesView : services page
- ContactView  : contact page with form
- handler404   : custom 404 page
"""
import re
from django.shortcuts import render, redirect
from django.views import View
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from shipments.models import Shipment


TOKEN_PATTERN = re.compile(r'^IGL-[A-Z0-9]{4}-[A-Z0-9]{4}$')

ADVICE_LIST = [
    _("Please ensure your delivery address and contact details are correct to avoid delays."),
    _("Kindly make sure you are available at the delivery location during the scheduled time."),
    _("For your security, please inspect your package upon delivery and report any issues immediately."),
    _("Always confirm payment details through our official website."),
    _("Providing accurate landmarks and phone numbers helps our delivery team reach you faster."),
    _("Your satisfaction is our priority. Stay available during delivery time for a smooth service."),
]


class HomeView(View):
    """
    Homepage. Handles the tracking token search form (GET submission).
    Validates token format client-side AND server-side before redirecting.
    """
    template_name = 'core/index.html'

    def get(self, request):
        token = request.GET.get('token', '').strip().upper()
        error = None

        if token:
            if not TOKEN_PATTERN.match(token):
                error = _('Invalid tracking code format. Expected format: IGL-XXXX-XXXX')
            elif not Shipment.objects.filter(tracking_token=token).exists():
                error = _('No shipment found for this tracking code. Please check and try again.')
            else:
                return redirect('track', token=token)

        return render(request, self.template_name, {
            'token': token,
            'error': error,
            'advice_list': ADVICE_LIST,
        })


class TrackView(View):
    """
    Displays the full tracking page for a given token.
    Shows masked sender/receiver info, current status, and event timeline.
    Returns a friendly 404-style page if token not found.
    """
    template_name = 'core/tracking.html'

    def get(self, request, token):
        token = token.upper()
        try:
            shipment = (
                Shipment.objects
                .select_related('sender', 'receiver')
                .prefetch_related('tracking_events__updated_by')
                .get(tracking_token=token)
            )
        except Shipment.DoesNotExist:
            return render(request, 'core/tracking_not_found.html', {'token': token}, status=404)

        # Build timeline (ordered oldest → newest for display)
        events = list(shipment.tracking_events.order_by('event_timestamp'))

        context = {
            'shipment': shipment,
            'events':   events,
            'sender':   getattr(shipment, 'sender', None),
            'receiver': getattr(shipment, 'receiver', None),
        }
        return render(request, self.template_name, context)


class AboutView(View):
    def get(self, request):
        return render(request, 'core/about.html')


class ServicesView(View):
    def get(self, request):
        return render(request, 'core/services.html')


class ContactView(View):
    template_name = 'core/contact.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # Contact form — store or email in v2; for now acknowledge receipt
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        if name and email and message:
            messages.success(request, _('Thank you for your message. We will get back to you shortly.'))
            return redirect('contact')
        messages.error(request, _('Please fill in all fields.'))
        return render(request, self.template_name)


def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    return render(request, 'errors/500.html', status=500)
