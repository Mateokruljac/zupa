"""Explicitni `schema_context` oko tenant CRUD-a.

Schema se uzima s `request.tenant` (thread-local) ili s trenutne konekcije.
"""
from __future__ import annotations

from contextlib import contextmanager
from functools import wraps

from django.db import connection, models


def current_schema_name() -> str:
    from django_tenants.utils import get_public_schema_name

    return getattr(connection, 'schema_name', None) or get_public_schema_name()


def resolve_tenant_schema_name(schema_name: str | None = None) -> str:
    from zupa.middleware.request_tenant import get_request

    if schema_name:
        return schema_name
    request = get_request()
    if request is not None:
        tenant = getattr(request, 'tenant', None)
        name = getattr(tenant, 'schema_name', None)
        if name:
            return name
    return current_schema_name()


@contextmanager
def tenant_context(schema_name: str | None = None):
    from django_tenants.utils import schema_context

    with schema_context(resolve_tenant_schema_name(schema_name)):
        yield


@contextmanager
def tenant_schema_only(schema_name: str | None = None):
    """PostgreSQL search_path samo tenant schema — bez `public` fallbacka."""
    from django_tenants.utils import get_public_schema_name

    resolved_name = resolve_tenant_schema_name(schema_name)
    public_schema = get_public_schema_name()
    previous_schema = getattr(connection, 'schema_name', public_schema)
    previous_include_public = getattr(connection, 'include_public_schema', True)
    try:
        if resolved_name == public_schema:
            connection.set_schema(public_schema, include_public=True)
        else:
            connection.set_schema(resolved_name, include_public=False)
        yield
    finally:
        connection.set_schema(previous_schema, include_public=previous_include_public)


@contextmanager
def run_in_tenant_schema(schema_name: str | None = None):
    with tenant_schema_only(schema_name):
        yield


def with_tenant_schema(func):
    """Na ulazu u CRUD funkciju postavi PostgreSQL schemu tenanta.

    Schema je `schema_name=` ako je predan (Celery), inače `request.tenant`
    ili trenutna konekcija.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        with tenant_context(kwargs.get('schema_name')):
            return func(*args, **kwargs)

    return wrapper


class TenantAwareQuerySet(models.QuerySet):
    def _fetch_all(self):
        with tenant_context():
            return super()._fetch_all()

    def exists(self):
        with tenant_context():
            return super().exists()

    def count(self):
        with tenant_context():
            return super().count()

    def get(self, *args, **kwargs):
        with tenant_context():
            return super().get(*args, **kwargs)

    def create(self, **kwargs):
        with tenant_context():
            return super().create(**kwargs)

    def bulk_create(self, *args, **kwargs):
        with tenant_context():
            return super().bulk_create(*args, **kwargs)

    def bulk_update(self, *args, **kwargs):
        with tenant_context():
            return super().bulk_update(*args, **kwargs)

    def get_or_create(self, *args, **kwargs):
        with tenant_context():
            return super().get_or_create(*args, **kwargs)

    def update_or_create(self, *args, **kwargs):
        with tenant_context():
            return super().update_or_create(*args, **kwargs)

    def update(self, **kwargs):
        with tenant_context():
            return super().update(**kwargs)

    def delete(self):
        with tenant_context():
            return super().delete()

    def aggregate(self, *args, **kwargs):
        with tenant_context():
            return super().aggregate(*args, **kwargs)

    def in_bulk(self, *args, **kwargs):
        with tenant_context():
            return super().in_bulk(*args, **kwargs)

    def iterator(self, *args, **kwargs):
        with tenant_context():
            yield from super().iterator(*args, **kwargs)

    def earliest(self, *args, **kwargs):
        with tenant_context():
            return super().earliest(*args, **kwargs)

    def latest(self, *args, **kwargs):
        with tenant_context():
            return super().latest(*args, **kwargs)

    def first(self):
        with tenant_context():
            return super().first()

    def last(self):
        with tenant_context():
            return super().last()


class TenantAwareManager(models.Manager.from_queryset(TenantAwareQuerySet)):
    pass


class TenantBoundModel(models.Model):
    """Abstract: save/delete i manager uvijek u `schema_context` tenanta."""

    objects = TenantAwareManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        with tenant_context():
            return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with tenant_context():
            return super().delete(*args, **kwargs)
