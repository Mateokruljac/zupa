"""HTTP viewovi za Pregled (nadzorna ploča)."""
from __future__ import annotations

from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from pastoral.decorators import pastoral_login_required
from pastoral.services.data import ParishDataService
from pregled.services.dashboard import build_dashboard_context


@pastoral_login_required
@require_http_methods(['GET', 'POST'])
def dashboard(request):
    parish_data_service = ParishDataService.for_request(request)
    if request.method == 'POST':
        action_name = request.POST.get('action')
        if action_name == 'toggle_task':
            from ured.api_actions import toggle_task

            parish_data = parish_data_service.load()
            toggle_task(parish_data, {'id': request.POST.get('task_id')})
            parish_data_service.save(parish_data)
            return redirect('pastoral:page', page='kalendar')

    parish_data = parish_data_service.load()
    request._pastoral_parish_data = parish_data
    page_context = build_dashboard_context(parish_data_service, parish_data)
    page_context['page_title'] = 'Početna'
    page_context['page_subtitle'] = 'Što danas radite u župi'
    page_context['current_page'] = 'dashboard'
    return render(request, 'pregled/dashboard.html', page_context)
