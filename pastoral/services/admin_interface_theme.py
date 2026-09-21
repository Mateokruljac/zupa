import re

from django.db import connection, transaction
from django_tenants.utils import get_public_schema_name

from django_multitenant.schema import with_tenant_schema


THEME_COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def _normalized_theme_color(color_value, fallback_color):
    normalized_color = str(color_value or '').strip()
    if THEME_COLOR_PATTERN.fullmatch(normalized_color):
        return normalized_color.upper()
    return fallback_color


def _mixed_theme_color(first_color, second_color, first_weight):
    first_components = tuple(
        int(first_color[index:index + 2], 16)
        for index in (1, 3, 5)
    )
    second_components = tuple(
        int(second_color[index:index + 2], 16)
        for index in (1, 3, 5)
    )
    mixed_components = tuple(
        round(
            first_component * first_weight
            + second_component * (1 - first_weight)
        )
        for first_component, second_component in zip(
            first_components,
            second_components,
        )
    )
    return '#' + ''.join(
        f'{component:02X}'
        for component in mixed_components
    )


@transaction.atomic
@with_tenant_schema
def synchronize_admin_interface_theme(primary_color, accent_color):
    """Usklađuje django-admin-interface Theme u schemi tenanta, ne u public."""
    from admin_interface.cache import del_cached_active_theme
    from admin_interface.models import Theme

    schema_name = getattr(connection, 'schema_name', None)
    if not schema_name or schema_name == get_public_schema_name():
        return None

    include_public = getattr(connection, 'include_public_schema', True)
    connection.set_schema(schema_name, include_public=False)
    try:
        return _write_tenant_admin_theme(
            Theme,
            del_cached_active_theme,
            primary_color,
            accent_color,
        )
    finally:
        connection.set_schema(schema_name, include_public=include_public)


def _write_tenant_admin_theme(
    Theme,
    del_cached_active_theme,
    primary_color,
    accent_color,
):
    normalized_primary_color = _normalized_theme_color(
        primary_color,
        '#5C2E3A',
    )
    normalized_accent_color = _normalized_theme_color(
        accent_color,
        '#B8922A',
    )
    darker_primary_color = _mixed_theme_color(
        normalized_primary_color,
        '#000000',
        0.84,
    )
    selected_background_color = _mixed_theme_color(
        normalized_accent_color,
        '#FFFFFF',
        0.22,
    )

    admin_theme = (
        Theme.objects.filter(active=True).order_by('pk').first()
        or Theme.objects.order_by('pk').first()
        or Theme(name='Pastoral')
    )
    if admin_theme.pk:
        Theme.objects.exclude(pk=admin_theme.pk).filter(active=True).update(
            active=False,
        )

    desired_theme_values = {
        'name': 'Pastoral',
        'active': True,
        'title': 'Pastoral — tehnička administracija',
        'title_visible': True,
        'title_color': normalized_accent_color,
        'logo_visible': False,
        'env_visible_in_header': False,
        'env_visible_in_favicon': False,
        'language_chooser_active': False,
        'css_header_background_color': normalized_primary_color,
        'css_header_text_color': '#FFFFFF',
        'css_header_link_color': '#FFFFFF',
        'css_header_link_hover_color': normalized_accent_color,
        'css_module_background_color': normalized_primary_color,
        'css_module_background_selected_color': selected_background_color,
        'css_module_text_color': '#FFFFFF',
        'css_module_link_color': '#FFFFFF',
        'css_module_link_selected_color': darker_primary_color,
        'css_module_link_hover_color': normalized_accent_color,
        'css_generic_link_color': normalized_primary_color,
        'css_generic_link_hover_color': darker_primary_color,
        'css_generic_link_active_color': normalized_accent_color,
        'css_save_button_background_color': normalized_primary_color,
        'css_save_button_background_hover_color': darker_primary_color,
        'css_save_button_text_color': '#FFFFFF',
    }
    theme_has_changes = admin_theme.pk is None
    for field_name, desired_value in desired_theme_values.items():
        if getattr(admin_theme, field_name) != desired_value:
            setattr(admin_theme, field_name, desired_value)
            theme_has_changes = True
    if theme_has_changes:
        admin_theme.save()
    del_cached_active_theme()
    return admin_theme
