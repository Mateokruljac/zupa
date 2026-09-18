from __future__ import annotations

from django.db import IntegrityError, connection, models
from django.test import TransactionTestCase

from core.models import OPEN_ENDED_VALID_TO, FCTA, SCD1, SCD2A


class ReferenceDimension(SCD1):
    code = models.CharField(max_length=20)

    class Meta:
        app_label = 'core'
        db_table = 'core_test_reference_dimension'


class StreetDimension(SCD2A):
    street_name = models.CharField(max_length=80)
    zone = models.CharField(max_length=40, blank=True)

    class Meta:
        app_label = 'core'
        db_table = 'core_test_street_dimension'


class IntentionFact(FCTA):
    intention_for = models.CharField(max_length=80)

    class Meta:
        app_label = 'core'
        db_table = 'core_test_intention_fact'


class DimensionalModelTests(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(ReferenceDimension)
            schema_editor.create_model(StreetDimension)
            schema_editor.create_model(IntentionFact)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(IntentionFact)
            schema_editor.delete_model(StreetDimension)
            schema_editor.delete_model(ReferenceDimension)
        super().tearDownClass()

    def test_scd1_save_new_writes_unified_key_and_content_hash(self):
        dimension = ReferenceDimension(code='HR-SB', is_active=True)
        dimension.save_new(unified_key_origin_fields=('code',))
        dimension.refresh_from_db()
        self.assertEqual(dimension.unified_key, 'HR-SB')
        self.assertEqual(len(dimension.content_hash), 64)

    def test_scd2_save_new_rejects_second_current_row(self):
        first_row = StreetDimension(street_name='Ilica', zone='centar')
        first_row.save_new(unified_key_origin_fields=('street_name',))
        duplicate = StreetDimension(street_name='Ilica', zone='zapad')
        with self.assertRaises(IntegrityError):
            duplicate.save_new(unified_key_origin_fields=('street_name',))

    def test_scd2_save_new_closes_previous_version_on_change(self):
        current_row = StreetDimension(street_name='Ilica', zone='centar')
        current_row.save_new(unified_key_origin_fields=('street_name',))
        current_row.zone = 'zapad'
        current_row.save_new(exclude=('is_active',))

        versions = list(
            StreetDimension.objects.filter(unified_key='Ilica').order_by('date_from')
        )
        self.assertEqual(len(versions), 2)
        self.assertNotEqual(versions[0].date_to, OPEN_ENDED_VALID_TO)
        self.assertEqual(versions[1].date_to, OPEN_ENDED_VALID_TO)
        self.assertEqual(versions[1].zone, 'zapad')
        self.assertTrue(versions[1].is_current)

    def test_fact_a_assigns_uuid_and_content_hash(self):
        fact = IntentionFact(intention_for='za župu')
        fact.save()
        fact.refresh_from_db()
        self.assertIsNotNone(fact.id)
        self.assertEqual(len(fact.content_hash), 64)
