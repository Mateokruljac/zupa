"""Premještaj legacy users/control_plane tablica u pastoral nakon uklanjanja tih appova.

User i Diocese su u stateu od 0001; ova migracija samo preimenuje postojeće tablice
(ili kreira ParishMembership ako treba).
"""
from __future__ import annotations

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models
from django.db.models import F, Q
from django.utils import timezone


def _rename_if_exists(schema_editor, old_name: str, new_name: str) -> None:
    table_names = set(schema_editor.connection.introspection.table_names())
    if old_name not in table_names or new_name in table_names:
        return
    schema_editor.execute(f'ALTER TABLE "{old_name}" RENAME TO "{new_name}"')


def rename_legacy_tables(apps, schema_editor):
    # User ostaje na users_user (Meta.db_table); samo control_plane tablice se preimenuju.
    _rename_if_exists(schema_editor, 'control_plane_diocese', 'pastoral_diocese')
    _rename_if_exists(
        schema_editor,
        'control_plane_parishmembership',
        'pastoral_parishmembership',
    )


def noop_reverse(apps, schema_editor):
    return None


class CreateModelIfNotExists(migrations.CreateModel):
    """CreateModel koji ne puca ako je tablica već nastala renameom legacy tablice."""

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        model = to_state.apps.get_model(app_label, self.name)
        if model._meta.db_table in schema_editor.connection.introspection.table_names():
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        model = from_state.apps.get_model(app_label, self.name)
        if model._meta.db_table not in schema_editor.connection.introspection.table_names():
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        ('pastoral', '0031_operational_parish_store'),
    ]

    operations = [
        migrations.RunPython(rename_legacy_tables, noop_reverse),
        CreateModelIfNotExists(
            name='ParishMembership',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('role', models.CharField(
                    choices=[
                        ('zupnik', 'Župnik'),
                        ('vikar', 'Župnik suradnik / vikar'),
                        ('upravitelj', 'Župni upravitelj'),
                        ('ured', 'Župni ured'),
                        ('financije', 'Financije'),
                        ('revizor', 'Revizor'),
                        ('biskupija', 'Biskupijski preglednik'),
                    ],
                    max_length=24,
                )),
                ('status', models.CharField(
                    choices=[
                        ('active', 'Aktivno'),
                        ('suspended', 'Suspendirano'),
                        ('revoked', 'Opozvano'),
                    ],
                    db_index=True,
                    default='active',
                    max_length=16,
                )),
                ('permission_set', models.JSONField(blank=True, default=dict)),
                ('valid_from', models.DateTimeField(default=timezone.now)),
                ('valid_until', models.DateTimeField(blank=True, null=True)),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('revocation_reason', models.TextField(blank=True)),
                ('approved_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='approved_parish_memberships',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('parish', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='memberships',
                    to='pastoral.parish',
                )),
                ('revoked_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='revoked_parish_memberships',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='parish_memberships',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Članstvo u župi',
                'verbose_name_plural': 'Članstva u župama',
                'ordering': ('parish', 'user__email'),
            },
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddConstraint(
                    model_name='parishmembership',
                    constraint=models.UniqueConstraint(
                        fields=('parish', 'user'),
                        name='control_unique_parish_user_membership',
                    ),
                ),
                migrations.AddConstraint(
                    model_name='parishmembership',
                    constraint=models.CheckConstraint(
                        condition=Q(valid_until__isnull=True) | Q(valid_until__gte=F('valid_from')),
                        name='control_membership_valid_period',
                    ),
                ),
                migrations.AddIndex(
                    model_name='parishmembership',
                    index=models.Index(
                        fields=['parish', 'status'],
                        name='control_mem_parish_status',
                    ),
                ),
                migrations.AddIndex(
                    model_name='parishmembership',
                    index=models.Index(
                        fields=['user', 'status'],
                        name='control_mem_user_status',
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
