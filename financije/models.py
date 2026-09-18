"""Financijski operativni zapisi (bivši Parish.data)."""
from core.models import FCTA, ContentHashedModel
from django.db import models


class FinanceSettings(ContentHashedModel):
    """Skalarni financijski parametri župe. SCD1 without a UUID PK."""

    parish = models.OneToOneField(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='finance_settings',
        primary_key=True,
    )
    lukno_default_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    unified_key = models.CharField(
        'Jedinstveni ključ',
        max_length=512,
        blank=True,
        db_index=True,
    )
    is_active = models.BooleanField('Aktivno', default=True, db_index=True)
    created_at = models.DateTimeField('Kreirano', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.unified_key = str(self.parish_id or self.unified_key)
        return super().save(*args, **kwargs)


class ParishDebt(FCTA):
    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='parish_debts',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    direction = models.CharField(max_length=20, blank=True, default='payable')
    year = models.PositiveIntegerField(null=True, blank=True)
    category = models.CharField(max_length=80, blank=True)
    label = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    contact = models.CharField(max_length=255, blank=True)
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]


class Invoice(FCTA):
    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='invoices',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    number = models.CharField(max_length=64, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    payer_name = models.CharField(max_length=255, blank=True)
    payer_address = models.CharField(max_length=255, blank=True)
    payer_oib = models.CharField(max_length=32, blank=True)
    category = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=40, blank=True)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_at = models.DateField(null=True, blank=True)
    linked_source = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    direction = models.CharField(max_length=40, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]


class CashbookEntry(FCTA):
    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='cashbook_entries',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    entry_date = models.DateField(null=True, blank=True, db_index=True)
    entry_type = models.CharField(max_length=20, blank=True, default='ulaz')
    category = models.CharField(max_length=80, blank=True)
    ledger = models.CharField(max_length=40, blank=True, default='crkveni')
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=40, blank=True)
    report_code = models.CharField(max_length=40, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]
