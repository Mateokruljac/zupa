"""Obrasci za dugovanja, blagajnu i ulazne račune."""
from decimal import Decimal

from django import forms

from financije.ledgers import (
    CASHBOOK_CATEGORY_CHOICES,
    DONATION_PURPOSE_CHOICES,
    LEDGER_CHOICES,
    LEDGER_CRKVENI,
)

_WIDGET = {'class': 'form-control'}
_MINIMUM_AMOUNT = Decimal('0.01')
_PAYABLE_CATEGORY_CHOICES = [
    ('režije', 'Režije'),
    ('dobavljaci', 'Dobavljači'),
    ('dz', 'Biskupija / DŽ'),
    ('ostalo', 'Ostalo'),
]


class ParishDebtForm(forms.Form):
    label = forms.CharField(
        label='Opis',
        max_length=200,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    amount = forms.DecimalField(
        label='Iznos (€)',
        max_digits=10,
        decimal_places=2,
        min_value=_MINIMUM_AMOUNT,
        widget=forms.NumberInput(attrs=_WIDGET),
    )
    category = forms.ChoiceField(
        label='Kategorija',
        choices=_PAYABLE_CATEGORY_CHOICES,
        widget=forms.Select(attrs=_WIDGET),
    )
    due_date = forms.DateField(
        label='Rok',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    contact = forms.CharField(
        label='Kontakt',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    notes = forms.CharField(
        label='Napomena',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, **_WIDGET}),
    )


class CashbookEntryForm(forms.Form):
    date = forms.DateField(
        label='Datum',
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    entry_type = forms.ChoiceField(
        label='Tip',
        choices=[('ulaz', 'Ulaz'), ('izlaz', 'Izlaz')],
        widget=forms.Select(attrs=_WIDGET),
    )
    ledger = forms.ChoiceField(
        label='Knjiga',
        choices=LEDGER_CHOICES,
        initial=LEDGER_CRKVENI,
        widget=forms.Select(attrs=_WIDGET),
    )
    category = forms.ChoiceField(
        label='Kategorija',
        choices=CASHBOOK_CATEGORY_CHOICES,
        widget=forms.Select(attrs=_WIDGET),
    )
    description = forms.CharField(
        label='Opis',
        max_length=200,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    amount = forms.DecimalField(
        label='Iznos (€)',
        max_digits=10,
        decimal_places=2,
        min_value=_MINIMUM_AMOUNT,
        widget=forms.NumberInput(attrs=_WIDGET),
    )
    payment_method = forms.ChoiceField(
        label='Način plaćanja',
        choices=[
            ('gotovina', 'Gotovina'),
            ('žiro', 'Žiro'),
            ('ostalo', 'Ostalo'),
        ],
        initial='gotovina',
        required=False,
        widget=forms.Select(attrs=_WIDGET),
    )


class DonationForm(forms.Form):
    date = forms.DateField(
        label='Datum',
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    donor = forms.CharField(
        label='Darovatelj',
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={
            **_WIDGET,
            'placeholder': 'Ime ili obitelj, ako je poznato',
        }),
    )
    amount = forms.DecimalField(
        label='Iznos (€)',
        max_digits=10,
        decimal_places=2,
        min_value=_MINIMUM_AMOUNT,
        widget=forms.NumberInput(attrs=_WIDGET),
    )
    purpose = forms.ChoiceField(
        label='Namjena',
        choices=DONATION_PURPOSE_CHOICES,
        initial=LEDGER_CRKVENI,
        widget=forms.Select(attrs=_WIDGET),
    )
    note = forms.CharField(
        label='Napomena',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            **_WIDGET,
            'placeholder': 'npr. za obnovu krova',
        }),
    )
    payment_method = forms.ChoiceField(
        label='Način plaćanja',
        choices=[
            ('gotovina', 'Gotovina'),
            ('žiro', 'Žiro'),
            ('ostalo', 'Ostalo'),
        ],
        initial='gotovina',
        required=False,
        widget=forms.Select(attrs=_WIDGET),
    )


class InvoiceForm(forms.Form):
    number = forms.CharField(
        label='Broj računa',
        max_length=60,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    issue_date = forms.DateField(
        label='Datum računa',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    due_date = forms.DateField(
        label='Rok plaćanja',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    supplier_name = forms.CharField(
        label='Dobavljač',
        max_length=120,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    category = forms.ChoiceField(
        label='Kategorija',
        choices=_PAYABLE_CATEGORY_CHOICES,
        widget=forms.Select(attrs=_WIDGET),
    )
    description = forms.CharField(
        label='Opis',
        max_length=200,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    amount = forms.DecimalField(
        label='Iznos (€)',
        max_digits=10,
        decimal_places=2,
        min_value=_MINIMUM_AMOUNT,
        widget=forms.NumberInput(attrs=_WIDGET),
    )

    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        due_date = cleaned_data.get('due_date')
        if issue_date and due_date and due_date < issue_date:
            self.add_error(
                'due_date',
                'Rok plaćanja ne može biti prije datuma računa.',
            )
        return cleaned_data
