"""
Inter Global Logistic — Root URL Configuration
Separates public site, admin portal, API, and Django admin URLs cleanly.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.utils.translation import gettext_lazy as _

# Customise Django admin header
admin.site.site_header = _('IGL Super Admin')
admin.site.site_title = _('Inter Global Logistic')
admin.site.index_title = _('System Administration')

urlpatterns = [
    # ── Django built-in Admin (Super Admin) ──────────────────────────────────
    path('django-admin/', admin.site.urls),

    # ── i18n language switcher ────────────────────────────────────────────────
    path('i18n/', include('django.conf.urls.i18n')),

    # ── Translation management (Rosetta) ─────────────────────────────────────
    path('rosetta/', include('rosetta.urls')),

    # ── REST API v1 ───────────────────────────────────────────────────────────
    path('api/v1/', include('shipments.api_urls')),

    # ── Admin Portal ──────────────────────────────────────────────────────────
    path('portal/', include('portal.urls')),

    # ── Public Site (core) — must be last so it catches / and /track/ ─────────
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
