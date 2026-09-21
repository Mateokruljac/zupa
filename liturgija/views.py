"""HTTP viewovi Liturgije — samo fasade prema pastoral shellu.

Pravi render/POST: `pastoral.views.admin_page_view`.
"""
from pastoral.domain_page_views import domain_page_view

nakane = domain_page_view('nakane')          # /pages/nakane/
mise = domain_page_view('mise')                # /pages/mise/
zupni_listic = domain_page_view('zupni-listic')  # /pages/zupni-listic/
