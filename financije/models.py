"""
Financijski operativni zapisi župe (bivši ključevi u Parish.data).

Četiri tablice: zadani iznos lukna, ručni dugovi, računi, retci blagajne.
Sakramentalni stipend i lukno obitelji nisu ovdje — žive na članstvu
kućanstva odnosno nakanama; ekran dugovanja ih samo agregira.

UI i dalje vidi camelCase dictove koje `operational_store` slaže preko
`finance_records`. `public_identifier` je id za UI; fizički PK je `id`.
`payload` je ostavština JSON-a, pri spremanju se prazni.
"""
from core.models import FCTA
from django.db import models


class FinanceSettings(models.Model):
    """
    Skalarni financijski parametri jedne župe.

    Zrno: jedna župa, jedan red (`OneToOne`, PK = parish id). Nije SCD2 —
    zadani iznos lukna se overwritea. Nije UUID SCD1 jer je PK već parish.

    Ne drži knjige ni retke blagajne.
    """

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
        help_text='Iznos lukna kad obiteljska godina nema vlastiti iznos.',
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
        """`unified_key` je id župe — nema drugog poslovnog ključa postavki."""
        self.unified_key = str(self.parish_id or self.unified_key)
        return super().save(*args, **kwargs)


class ParishDebt(FCTA):
    """
    Ručna financijska stavka: župa duguje ili joj se duguje.

    Zrno: jedna stavka po `public_identifier` unutar župe. Nije lukno,
    nakana ni račun — samo unos koji nema drugi izvorni zapis
    (`parishDebts` u starom JSON-u). FCTA: ispravak je novi događaj ili
    zastavica `is_paid`, ne nova verzija dimenzije.

    `direction`: `payable` (župa duguje) ili `receivable`.
    """

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
    """
    Račun župe (ulazni od dobavljača ili izlazni, `direction`).

    Zrno: jedan račun po `public_identifier`. `payer_name` drži i naziv
    dobavljača i naziv platitelja — UI i dalje šalje `supplierName` /
    `payerName`. `linked_source` veže račun na drugi operativni zapis
    ako postoji. Statusi su hrvatski kodovi UI-ja (`primljen`, `placen`).

    Plaćanje računa ne knjiži samo od sebe red blagajne.
    """

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
    """
    Jedan red jedne od četiri knjige računa.

    Zrno: jedan knjiženi iznos (`ulaz`/`izlaz`) na datum, u `ledger`.
    Župni saldo čita samo knjigu `crkveni`. Kategorija i ledger moraju
    proći `normalize_ledger` pri upisu. FCTA: storno je novi red ili
    ispravak iznosa, ne SCD2 verzija.

    `report_code` je oznaka za vanjsko izvješće, nije knjiga.
    """

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
