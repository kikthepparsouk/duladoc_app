"""
SEO context processors for passing meta tags to templates
"""
from django.conf import settings


def seo_context(request):
    """
    Add SEO context to all templates
    Usage: {{ seo.site_name }} in templates
    """
    return {
        'seo': {
            'site_name': settings.SITE_NAME,
            'site_domain': settings.SITE_DOMAIN,
            'site_protocol': settings.META_SITE_PROTOCOL,
            'site_url': settings.SITE_URL,
        }
    }
