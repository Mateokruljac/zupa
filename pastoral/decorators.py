from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

from pastoral.services.permissions import can_access_page, is_locked_finance_page


def pastoral_login_required(view_function):
    @login_required(login_url='pastoral:login')
    @wraps(view_function)
    def wrapper(request, *args, **kwargs):
        # Domenski URL viewovi povijesno su slug prosljeđivali kao prvi
        # pozicijski argument. Ovlast mora čitati oba oblika; inače bi takav
        # zahtjev izgledao kao dashboard i zaobišao zabranu modula.
        resolver_match = getattr(request, 'resolver_match', None)
        page = kwargs.get('page') or (args[0] if args else None)
        if page is None and resolver_match:
            resolver_kwargs = getattr(resolver_match, 'kwargs', {}) or {}
            page = (
                resolver_kwargs.get('page')
                or getattr(resolver_match, 'url_name', None)
            )
        if page in {None, 'app'}:
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
