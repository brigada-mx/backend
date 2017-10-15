from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone


def base(request):
    return {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'client_contact_email': settings.CLIENT_CONTACT_EMAIL,
        'nurse_contact_email': settings.NURSE_CONTACT_EMAIL,
        'contact_phone': settings.CONTACT_PHONE,
        'contact_address': settings.CONTACT_ADDRESS,
        'current_date': timezone.localtime(timezone.now()).date(),
        'current_datetime': timezone.localtime(timezone.now()),

        'nurse_app_android_url': settings.NURSE_APP_ANDROID_URL,
        'client_app_android_url': settings.CLIENT_APP_ANDROID_URL,
        'nurse_app_ios_url': settings.NURSE_APP_IOS_URL,
        'client_app_ios_url': settings.CLIENT_APP_IOS_URL,
    }


def render_to_string_(template_name, context=None, **kwargs):
    """Adds context to `render_to_string`, which doesn't pull in global context
    from context processors the way `render` does.

    `context` passed in kwargs takes precedence.
    """
    base_context = base(None)
    context = context or {}
    base_context.update(context)
    return render_to_string(template_name, context=base_context, **kwargs)
