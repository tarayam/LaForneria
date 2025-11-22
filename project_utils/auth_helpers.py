from functools import wraps
from django.shortcuts import redirect
from django.conf import settings
from django.utils import timezone


def reauth_required(view_func):
    """Decorator that requires the user to have reauthenticated recently.

    Behavior:
    - If user is not authenticated -> redirect to LOGIN_URL with next.
    - If user is authenticated but session key `reauthenticated_at` missing or expired ->
      redirect to confirm-password page with `next` param set to current path.
    - Otherwise proceed to the view.
    """

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        # Not authenticated -> go to login
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.get_full_path()}")

        # Check reauth timestamp
        ts = request.session.get('reauthenticated_at')
        timeout = getattr(settings, 'REAUTHENTICATE_TIMEOUT', 300)
        now_ts = timezone.now().timestamp()

        if not ts:
            return redirect(f"/confirm-password/?next={request.get_full_path()}")

        try:
            ts = float(ts)
        except Exception:
            return redirect(f"/confirm-password/?next={request.get_full_path()}")

        if (now_ts - ts) > timeout:
            return redirect(f"/confirm-password/?next={request.get_full_path()}")

        return view_func(request, *args, **kwargs)

    return _wrapped
