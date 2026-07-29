from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

from pastoral.services.permissions import can_access_page, is_locked_finance_page


def pastoral_login_required(view_func):
    @login_required(login_url='pastoral:login')
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        page = kwargs.get('page', 'dashboard')
        if request.resolver_match.url_name == 'app':
            page = 'dashboard'
        if not can_access_page(page, request.user.role):
            if is_locked_finance_page(page):
                messages.error(request, 'Ovaj financijski modul je zaključan za vašu ulogu.')
            else:
                messages.error(request, 'Nemate pristup ovom modulu.')
            return redirect('pastoral:app')
        return view_func(request, *args, **kwargs)
    return wrapper
