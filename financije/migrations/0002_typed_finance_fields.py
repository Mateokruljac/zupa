# Generated manually — tipizirana polja financija + backfill iz payload-a.

from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import migrations, models


def _parse_iso_date(value):
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _decimal_amount(value):
    try:
        return Decimal(str(value if value is not None else 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def backfill_typed_finance_fields(apps, schema_editor):
    ParishDebt = apps.get_model('financije', 'ParishDebt')
    Invoice = apps.get_model('financije', 'Invoice')
    CashbookEntry = apps.get_model('financije', 'CashbookEntry')

    for debt in ParishDebt.objects.all().iterator():
        payload = debt.payload or {}
        year_raw = payload.get('year')
        try:
            year_value = int(year_raw) if year_raw not in (None, '') else None
        except (TypeError, ValueError):
            year_value = None
        debt.direction = str(payload.get('direction') or 'payable')
        debt.year = year_value
        debt.category = str(payload.get('category') or '')
        debt.label = str(payload.get('label') or '')
        debt.amount = _decimal_amount(payload.get('amount'))
        debt.is_paid = bool(payload.get('paid'))
        debt.contact = str(payload.get('contact') or '')
        debt.due_date = _parse_iso_date(payload.get('dueDate'))
        debt.notes = str(payload.get('notes') or '')
        debt.payload = {}
        debt.save()

    for invoice in Invoice.objects.all().iterator():
        payload = invoice.payload or {}
        linked_source = payload.get('linkedSource')
        if not isinstance(linked_source, dict):
            linked_source = {}
        invoice.number = str(payload.get('number') or '')
        invoice.issue_date = _parse_iso_date(payload.get('issueDate'))
        invoice.due_date = _parse_iso_date(payload.get('dueDate'))
        invoice.payer_name = str(payload.get('payerName') or '')
        invoice.payer_address = str(payload.get('payerAddress') or '')
        invoice.payer_oib = str(payload.get('payerOib') or '')
        invoice.category = str(payload.get('category') or '')
        invoice.description = str(payload.get('description') or '')
        invoice.amount = _decimal_amount(payload.get('amount'))
        invoice.vat_rate = _decimal_amount(payload.get('vatRate'))
        invoice.total = _decimal_amount(payload.get('total'))
        invoice.status = str(payload.get('status') or '')
        invoice.paid_amount = _decimal_amount(payload.get('paidAmount'))
        invoice.paid_at = _parse_iso_date(payload.get('paidAt'))
        invoice.linked_source = linked_source
        invoice.notes = str(payload.get('notes') or '')
        invoice.direction = str(payload.get('direction') or '')
        invoice.payload = {}
        invoice.save()

    for entry in CashbookEntry.objects.all().iterator():
        payload = entry.payload or {}
        entry.entry_date = _parse_iso_date(payload.get('date'))
        entry.entry_type = str(payload.get('type') or 'ulaz')
        entry.category = str(payload.get('category') or '')
        entry.ledger = str(payload.get('ledger') or 'plavi')
        entry.description = str(payload.get('description') or '')
        entry.amount = _decimal_amount(payload.get('amount'))
        entry.payment_method = str(payload.get('paymentMethod') or '')
        entry.report_code = str(payload.get('reportCode') or '')
        entry.payload = {}
        entry.save()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('financije', '0001_operational_parish_store'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashbookentry',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='cashbookentry',
            name='category',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='cashbookentry',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='cashbookentry',
            name='entry_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='cashbookentry',
            name='entry_type',
            field=models.CharField(blank=True, default='ulaz', max_length=20),
        ),
        migrations.AddField(
            model_name='cashbookentry',
            name='ledger',
            field=models.CharField(blank=True, default='plavi', max_length=40),
        ),
        migrations.AddField(
            model_name='cashbookentry',
            name='payment_method',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='cashbookentry',
            name='report_code',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='invoice',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='invoice',
            name='category',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='invoice',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='direction',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='invoice',
            name='due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='issue_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='linked_source',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='invoice',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='number',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='invoice',
            name='paid_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='invoice',
            name='paid_at',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='payer_address',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='invoice',
            name='payer_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='invoice',
            name='payer_oib',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='invoice',
            name='status',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='invoice',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='invoice',
            name='vat_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6),
        ),
        migrations.AddField(
            model_name='parishdebt',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='parishdebt',
            name='category',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='parishdebt',
            name='contact',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='parishdebt',
            name='direction',
            field=models.CharField(blank=True, default='payable', max_length=20),
        ),
        migrations.AddField(
            model_name='parishdebt',
            name='due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='parishdebt',
            name='is_paid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='parishdebt',
            name='label',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='parishdebt',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='parishdebt',
            name='year',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_typed_finance_fields, noop_reverse),
    ]
