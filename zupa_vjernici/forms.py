"""Obrasci za obitelji, ulice i pastoralne posjete."""
from django import forms

_WIDGET = {'class': 'form-control'}


class FamilyForm(forms.Form):
    surname = forms.CharField(
        label='Prezime obitelji',
        max_length=120,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    street_id = forms.ChoiceField(
        label='Ulica',
        choices=(),
        required=False,
        widget=forms.Select(attrs=_WIDGET),
    )
    address = forms.CharField(
        label='Kućni broj i dodatak adresi',
        max_length=200,
        widget=forms.TextInput(attrs={
            **_WIDGET,
            'placeholder': 'npr. 24 A',
        }),
    )
    phone = forms.CharField(
        label='Telefon',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    email = forms.EmailField(
        label='E-mail',
        required=False,
        widget=forms.EmailInput(attrs=_WIDGET),
    )
    origin_place = forms.CharField(
        label='Mjesto podrijetla',
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    status = forms.ChoiceField(
        label='Status kartona',
        choices=(('aktivna', 'Aktivna obitelj'), ('neaktivna', 'Neaktivna obitelj')),
        initial='aktivna',
        required=False,
        widget=forms.Select(attrs=_WIDGET),
    )
    pastoral_notes = forms.CharField(
        label='Pastoralna bilješka',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, **_WIDGET}),
    )

    def __init__(self, *args, streets=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['street_id'].choices = [('', '— Bez povezane ulice —')] + [
            (street.get('id'), street.get('name', ''))
            for street in (streets or [])
            if street.get('id')
        ]


class FamilyMemberForm(forms.Form):
    name = forms.CharField(
        label='Ime i prezime',
        max_length=140,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    relation = forms.CharField(
        label='Odnos u obitelji',
        max_length=80,
        required=False,
        widget=forms.TextInput(attrs={
            **_WIDGET,
            'placeholder': 'npr. suprug, supruga, dijete',
        }),
    )
    birth_year = forms.IntegerField(
        label='Godina rođenja',
        min_value=1900,
        required=False,
        widget=forms.NumberInput(attrs=_WIDGET),
    )


class FamilyContributionForm(forms.Form):
    year = forms.IntegerField(
        label='Godina',
        min_value=1990,
        max_value=2100,
        widget=forms.NumberInput(attrs=_WIDGET),
    )
    lukno_amount = forms.DecimalField(
        label='Lukno (€)',
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={**_WIDGET, 'step': '0.01'}),
    )
    lukno_paid = forms.BooleanField(
        label='Lukno plaćeno',
        required=False,
    )
    lukno_paid_at = forms.DateField(
        label='Datum uplate lukna',
        required=False,
        widget=forms.DateInput(attrs={**_WIDGET, 'type': 'date'}),
    )
    church_donation = forms.DecimalField(
        label='Dar za crkvu (€)',
        min_value=0,
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={**_WIDGET, 'step': '0.01'}),
    )
    donation_date = forms.DateField(
        label='Datum dara',
        required=False,
        widget=forms.DateInput(attrs={**_WIDGET, 'type': 'date'}),
    )
    notes = forms.CharField(
        label='Bilješka',
        required=False,
        widget=forms.TextInput(attrs=_WIDGET),
    )


class FamilyNotesForm(forms.Form):
    pastoral_notes = forms.CharField(
        label='Pastoralna bilješka',
        required=False,
        widget=forms.Textarea(attrs={'rows': 5, **_WIDGET}),
    )


class StreetForm(forms.Form):
    name = forms.CharField(label='Naziv ulice', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    zone = forms.CharField(label='Zona / kvart', max_length=80, required=False, widget=forms.TextInput(attrs=_WIDGET))
    notes = forms.CharField(label='Napomena', required=False, widget=forms.Textarea(attrs={'rows': 2, **_WIDGET}))

class VisitForm(forms.Form):
    scheduled = forms.DateField(label='Datum posjeta', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    person = forms.CharField(label='Osoba / obitelj', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    visit_type = forms.ChoiceField(
        label='Vrsta',
        choices=[
            ('obitelj', 'Pastoralni posjet obitelji'),
            ('kucna-pricest', 'Kućna sv. Pričest'),
            ('bolnica', 'Posjet bolesniku'),
            ('ostalo', 'Ostalo'),
        ],
        widget=forms.Select(attrs=_WIDGET),
    )
    address = forms.CharField(label='Adresa', max_length=200, required=False, widget=forms.TextInput(attrs=_WIDGET))
    priest = forms.CharField(label='Svećenik', max_length=100, required=False, widget=forms.TextInput(attrs=_WIDGET))
    purpose = forms.CharField(label='Svrha / napomena', max_length=200, required=False, widget=forms.TextInput(attrs=_WIDGET))
    family_id = forms.CharField(
        label='Povezana obitelj',
        max_length=40,
        required=False,
        widget=forms.Select(attrs=_WIDGET),
    )
    report = forms.CharField(label='Izvještaj', required=False, widget=forms.Textarea(attrs={'rows': 3, **_WIDGET}))

    def __init__(self, *args, families=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['family_id'].widget.choices = [
            ('', '— Posjet nije vezan uz obitelj —'),
            *[
                (
                    family.get('id'),
                    ' · '.join(filter(None, (
                        family.get('surname', ''),
                        family.get('address', ''),
                    ))),
                )
                for family in (families or [])
                if family.get('id')
            ],
        ]

