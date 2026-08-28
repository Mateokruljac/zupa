"""Vrati User tablicu na users_user ako ju je 0032 preimenovao u pastoral_user."""

from django.db import migrations


def _rename_if_exists(schema_editor, old_name: str, new_name: str) -> None:
    table_names = set(schema_editor.connection.introspection.table_names())
    if old_name not in table_names or new_name in table_names:
        return
    schema_editor.execute(f'ALTER TABLE "{old_name}" RENAME TO "{new_name}"')


def rename_pastoral_user_to_users_user(apps, schema_editor):
    _rename_if_exists(schema_editor, 'pastoral_user', 'users_user')
    _rename_if_exists(schema_editor, 'pastoral_user_groups', 'users_user_groups')
    _rename_if_exists(
        schema_editor,
        'pastoral_user_user_permissions',
        'users_user_user_permissions',
    )


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ('pastoral', '0033_alter_user_managers_alter_user_groups'),
    ]

    operations = [
        migrations.RunPython(rename_pastoral_user_to_users_user, noop_reverse),
    ]
