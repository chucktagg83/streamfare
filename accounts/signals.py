from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import LoginRecord, Profile


def get_client_ip(request):
    """
    Try to find the user's IP address.

    HTTP_X_FORWARDED_FOR may exist when the site is behind
    a reverse proxy or hosting platform.

    REMOTE_ADDR is the normal direct IP value.
    """

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded_for:
        # There may be multiple addresses separated by commas.
        # The first address is usually the original client.
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.META.get("REMOTE_ADDR")

    return ip_address


@receiver(user_logged_in)
def record_successful_login(sender, request, user, **kwargs):
    """
    Runs automatically after a successful login.
    """

    # Make sure the user has a profile.
    Profile.objects.get_or_create(user=user)

    # Read the browser information from the request.
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    # Save the login history.
    LoginRecord.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        user_agent=user_agent,
    )