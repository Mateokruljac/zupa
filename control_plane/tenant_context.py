from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TenantContext:
    tenant_id: UUID
    parish_pk: int
    database_alias: str | None
    membership_id: UUID | None
    actor_id: UUID
    role: str
    used_legacy_fallback: bool = False


_active_tenant = ContextVar('pastoral_active_tenant', default=None)


def get_current_tenant_context():
    return _active_tenant.get()


def set_current_tenant_context(context):
    return _active_tenant.set(context)


def reset_current_tenant_context(token):
    _active_tenant.reset(token)
