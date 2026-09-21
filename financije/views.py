"""
HTTP ulazi stranica Financija u pastoral shellu.

Svaki view je `domain_page_view(slug)`: URL ostaje `/pages/<slug>/`,
render i POST idu kroz `pastoral.views.admin_page_view`. Prava, tenant
i izbor predloška nisu ovdje. Kad financije dobiju vlastiti URL prostor,
ove fasade se zamjenjuju lokalnim viewovima, slugovi predložaka ostaju.
"""
from pastoral.domain_page_views import domain_page_view

dugovanja = domain_page_view('dugovanja')
dugovanja.__doc__ = (
    """Ekran potraživanja prema župi i obveza župe (`dugovanja`)."""
)

blagajna = domain_page_view('blagajna')
blagajna.__doc__ = (
    """Ekran četiri knjige računa (`blagajna`)."""
)

racuni = domain_page_view('racuni')
racuni.__doc__ = (
    """Ekran ulaznih računa dobavljača (`racuni`)."""
)

financijska_izvjestaja = domain_page_view('financijska-izvjestaja')
financijska_izvjestaja.__doc__ = (
    """Operativni financijski pregled godine (`financijska-izvjestaja`)."""
)
