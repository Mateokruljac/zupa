"""HTTP viewovi za Župa i vjernici."""
from pastoral.decorators import pastoral_login_required
from pastoral.domain_page_views import domain_page_view
from pastoral.views import admin_page_view


@pastoral_login_required
def obitelji(request):
    if request.method == 'GET' and request.GET.get('export') == 'xlsx':
        from pastoral.services.data import ParishDataService
        from zupa_vjernici.services.families_export import families_xlsx_response

        parish_data = ParishDataService.for_request(request).load()
        return families_xlsx_response(parish_data, request)
    return admin_page_view(request, 'obitelji')


ulice = domain_page_view('ulice')
posjete = domain_page_view('posjete')
