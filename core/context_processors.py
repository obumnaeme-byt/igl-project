"""
Global template context available to every template.
Injects site name and supported languages without repeating in every view.
"""
from django.conf import settings
from django.utils import translation


def site_settings(request):
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'Inter Global Logistic'),
        'SUPPORT_EMAIL': getattr(settings, 'SUPPORT_EMAIL', ''),
        'LANGUAGES': settings.LANGUAGES,
        'CURRENT_LANGUAGE': translation.get_language(),
    }
