"""Factory za page viewove domena koji i dalje koriste pastoral shell."""
from __future__ import annotations

from collections.abc import Callable


def domain_page_view(page_slug: str) -> Callable:
    """Vrati view koji renderira admin stranicu preko pastoral shella.

    URL i ponašanje ostaju isti (`/pages/<slug>/`). Kad domena preuzme
    vlastiti view stack, ova fasada se zamjenjuje lokalnom implementacijom.
    """

    def page_view(request, page: str | None = None):
        from pastoral.views import admin_page_view

        return admin_page_view(request, page or page_slug)

    page_view.__name__ = page_slug.replace('-', '_')
    page_view.__qualname__ = page_view.__name__
    page_view.__doc__ = f'Admin stranica `{page_slug}`.'
    return page_view
