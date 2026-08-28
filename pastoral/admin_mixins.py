"""Zajednički Django admin mixini za tehničku administraciju."""


class ProtectedReferenceAdminMixin:
    """Šifrarnici i predlošci — bez brisanja; dostupno staffu župe."""

    def has_module_permission(self, request):
        return bool(request.user.is_active and request.user.is_staff)

    def has_view_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_staff)

    def has_add_permission(self, request):
        return bool(request.user.is_active and request.user.is_staff)

    def has_change_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_staff)

    def has_delete_permission(self, request, obj=None):
        return False


class ParishTechnicalAdminMixin:
    """Periodična konfiguracija župe — svi aktivni staff korisnici."""

    def has_module_permission(self, request):
        return bool(request.user.is_active and request.user.is_staff)

    def has_view_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_staff)

    def has_add_permission(self, request):
        return bool(request.user.is_active and request.user.is_staff)

    def has_change_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_staff)

    def has_delete_permission(self, request, obj=None):
        return False
