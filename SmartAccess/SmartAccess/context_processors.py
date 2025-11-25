"""
Custom context processors for SmartAccess project
These make variables available in all templates
"""
from django.conf import settings


def raspberry_pi_config(request):
    """
    Add Raspberry Pi configuration to all template contexts
    Usage in templates: {{ RASPBERRY_PI_URL }}
    """
    return {
        'RASPBERRY_PI_IP': settings.RASPBERRY_PI_IP,
        'RASPBERRY_PI_PORT': settings.RASPBERRY_PI_PORT,
        'RASPBERRY_PI_URL': settings.RASPBERRY_PI_URL,
    }
