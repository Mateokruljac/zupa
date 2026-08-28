"""Registar kontekst-buildera za admin stranice pastoral shella.

Domene registriraju svoje stranice; pastoral samo sastavlja zajednički omotač.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from pastoral.services.data import ParishDataService

PageContextBuilder = Callable[
    [object, dict, 'ParishDataService'],
    dict,
]

PAGE_META: dict[str, tuple[str, str]] = {}
PAGE_CONTEXT_BUILDERS: dict[str, PageContextBuilder] = {}

_MVP_LOADED = False
_PHASE_TWO_LOADED = False


def register_page(
    slug: str,
    *,
    title: str,
    subtitle: str = '',
) -> Callable[[PageContextBuilder], PageContextBuilder]:
    """Registrira builder i meta podatke za jednu admin stranicu."""

    def decorator(builder: PageContextBuilder) -> PageContextBuilder:
        if slug in PAGE_CONTEXT_BUILDERS:
            raise ValueError(f'Stranica {slug!r} je već registrirana.')
        PAGE_META[slug] = (title, subtitle)
        PAGE_CONTEXT_BUILDERS[slug] = builder
        return builder

    return decorator


def page_title_subtitle(slug: str) -> tuple[str, str]:
    ensure_page_contexts_loaded()
    return PAGE_META.get(slug, (slug.replace('-', ' ').title(), ''))


def get_page_context_builder(slug: str) -> PageContextBuilder | None:
    ensure_page_contexts_loaded()
    return PAGE_CONTEXT_BUILDERS.get(slug)


def ensure_page_contexts_loaded() -> None:
    """Učitava MVP buildere jednom; faza 2 samo kada je modul dostupan."""
    global _MVP_LOADED, _PHASE_TWO_LOADED
    if not _MVP_LOADED:
        # Side-effect uvozi: @register_page u domain modulima.
        import financije.page_contexts  # noqa: F401
        import isprave.page_contexts  # noqa: F401
        import liturgija.page_contexts  # noqa: F401
        import sakramenti.page_contexts  # noqa: F401
        import ured.page_contexts  # noqa: F401
        import zupa_vjernici.page_contexts  # noqa: F401

        _MVP_LOADED = True

    if _PHASE_TWO_LOADED:
        return

    from phase_two.module_registry import PRODUCT_MODULES

    if not any(product_module.is_available for product_module in PRODUCT_MODULES):
        return

    try:
        import phase_two.page_contexts  # noqa: F401
    except ModuleNotFoundError:
        pass
    _PHASE_TWO_LOADED = True
