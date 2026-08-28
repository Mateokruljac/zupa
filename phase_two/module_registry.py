"""Privremeni stub — phase_two paket je uklonjen iz MVP treea."""
from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class ProductModule:
    key: str
    label: str
    release_phase: int
    pages: frozenset[str]
    icon: str = ''
    summary: str = ''
    planned_features: tuple[str, ...] = ()

    @property
    def is_available(self) -> bool:
        return settings.PASTORAL_PRODUCT_PHASE >= self.release_phase


INTERPARISH_COLLABORATION_MODULE = ProductModule(
    key='interparish-collaboration',
    label='Međužupna suradnja',
    release_phase=2,
    pages=frozenset({'dekanat'}),
)

OPERATIONS_CENTER_MODULE = ProductModule(
    key='operations-center',
    label='Operativno središte',
    release_phase=2,
    pages=frozenset({'operativno-srediste'}),
)

PRODUCT_MODULES = (
    INTERPARISH_COLLABORATION_MODULE,
    OPERATIONS_CENTER_MODULE,
)


def module_for_page(page: str) -> ProductModule | None:
    return next(
        (
            product_module
            for product_module in PRODUCT_MODULES
            if page in product_module.pages
        ),
        None,
    )


def is_page_available(page: str) -> bool:
    product_module = module_for_page(page)
    return product_module is None or product_module.is_available
