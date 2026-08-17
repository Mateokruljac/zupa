import logging

from django import template
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.urls import NoReverseMatch, reverse


register = template.Library()
logger = logging.getLogger(__name__)


def _model_from_label(model_label):
    try:
        app_label, model_name = model_label.split('.', 1)
        return apps.get_model(app_label, model_name)
    except (LookupError, ValueError):
        logger.warning('ADMIN_REORDER sadrži nepoznat model: %s', model_label)
        return None


def _model_info(model, request):
    model_admin = admin.site._registry.get(model)
    if not model_admin or not model_admin.has_view_permission(request):
        return None

    opts = model._meta
    try:
        url = reverse(f'admin:{opts.app_label}_{opts.model_name}_changelist')
    except NoReverseMatch:
        return None

    add_url = None
    if model_admin.has_add_permission(request):
        try:
            add_url = reverse(f'admin:{opts.app_label}_{opts.model_name}_add')
        except NoReverseMatch:
            pass

    return {
        'name': opts.verbose_name_plural or opts.verbose_name,
        'object_name': opts.object_name,
        'app_label': opts.app_label,
        'model_name': opts.model_name,
        'url': url,
        'add_url': add_url,
    }


@register.simple_tag(takes_context=True)
def get_admin_reorder_groups(context):
    request = context.get('request')
    if not request:
        return []

    groups = []
    for position, config in enumerate(getattr(settings, 'ADMIN_REORDER', ()), start=1):
        models = []
        for model_label in config.get('models', ()):
            model = _model_from_label(model_label)
            info = _model_info(model, request) if model else None
            if info:
                models.append(info)
        if models:
            groups.append({
                'id': f'admin-group-{position}',
                'label': config.get('label', ''),
                'description': config.get('description', ''),
                'models': models,
            })
    return groups
