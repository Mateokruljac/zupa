from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

from pastoral.services.permissions import can_access_page, is_locked_finance_page


def pastoral_login_required(view_function):
    @login_required(login_url='pastoral:login')
    @wraps(view_function)
    def wrapper(request, *args, **kwargs):
        page = kwargs.get('page', 'dashboard')
        if request.resolver_match.url_name == 'app':
            page = 'dashboard'
        tenant_context = getattr(request, 'tenant_context', None)
        active_role = tenant_context.role if tenant_context else request.user.role
        if not can_access_page(page, active_role):
            if is_locked_finance_page(page):
                messages.error(request, 'Ovaj financijski modul je zaključan za vašu ulogu.')
            else:
                messages.error(request, 'Nemate pristup ovom modulu.')
            return redirect('pastoral:app')
        return view_function(request, *args, **kwargs)
    return wrapper
