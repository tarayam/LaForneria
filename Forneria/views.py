from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.urls import reverse


def login_view(request):
    """Simple login view: muestra formulario y valida credenciales."""
    error_message = None
    username = ''

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            error_message = 'Usuario o contraseña incorrectos.'

    return render(request, 'login.html', {
        'error_message': error_message,
        'username': username,
    })


@login_required
def confirm_password(request):
    """View that asks the logged-in user to re-enter their password.
    On success sets a session flag `reauthenticated_at` and redirects to `next`.
    """
    error_message = None
    next_url = request.GET.get('next') or request.POST.get('next') or settings.LOGIN_REDIRECT_URL

    if request.method == 'POST':
        password = request.POST.get('password', '')
        user = authenticate(request, username=request.user.username, password=password)
        if user is not None:
            # mark reauthentication time
            request.session['reauthenticated_at'] = timezone.now().timestamp()
            # keep session saved
            request.session.modified = True
            return redirect(next_url)
        else:
            error_message = 'Contraseña incorrecta. Intenta nuevamente.'

    return render(request, 'confirm_password.html', {
        'error_message': error_message,
        'next': next_url,
    })
