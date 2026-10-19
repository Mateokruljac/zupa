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
        label='Kućni broj (Kat stana)',
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
    status = forms.ChoiceField(
        label='Status kartona',
        choices=(
            ('aktivna', 'Aktivna — u redovnoj skrbi'),
            ('neaktivna', 'Neaktivna — odseljeni / zatvoren karton'),
        ),
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


FAMILY_MEMBER_RELATIONS = (
    ('', '— Odaberite odnos —'),
    ('Samačko kućanstvo', 'Samačko kućanstvo'),
    ('suprug/otac', 'suprug/otac'),
    ('supruga/majka', 'supruga/majka'),
    ('dijete', 'dijete'),
    ('drugo', 'drugo'),
)


class FamilyMemberForm(forms.Form):
    given_name = forms.CharField(
        label='Ime',
        max_length=80,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    surname = forms.CharField(
        label='Prezime',
        max_length=80,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    relation = forms.ChoiceField(
        label='Odnos u obitelji',
        choices=FAMILY_MEMBER_RELATIONS,
        widget=forms.Select(attrs=_WIDGET),
    )
    birth_date = forms.DateField(
        label='Datum rođenja',
        required=False,
        widget=forms.DateInput(attrs={**_WIDGET, 'type': 'date'}),
    )
    notes = forms.CharField(
        label='Bilješka',
        required=False,
        widget=forms.Textarea(attrs={**_WIDGET, 'rows': 3}),
    )


CONTRIBUTION_CATEGORY_CHOICES = (
    ('lukno', 'Lukno'),
    ('obiteljski_dar', 'Obiteljski dar'),
    ('zvonarina', 'Zvonarina'),
    ('ostalo', 'Ostalo'),
)


class FamilyContributionForm(forms.Form):
    contribution_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )
    year = forms.IntegerField(
        label='Godina',
        min_value=1990,
        max_value=2100,
        widget=forms.NumberInput(attrs=_WIDGET),
    )
    category = forms.ChoiceField(
        label='Kategorija',
        choices=CONTRIBUTION_CATEGORY_CHOICES,
        initial='lukno',
        widget=forms.Select(attrs=_WIDGET),
    )
    amount = forms.DecimalField(
        label='Iznos (€)',
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={**_WIDGET, 'step': '0.01'}),
    )
    paid_at = forms.DateField(
        label='Datum uplate',
        widget=forms.DateInput(attrs={**_WIDGET, 'type': 'date'}),
    )
    notes = forms.CharField(
        label='Bilješka',
        required=False,
        widget=forms.Textarea(attrs={**_WIDGET, 'rows': 3}),
    )


class FamilyNotesForm(forms.Form):
    pastoral_notes = forms.CharField(
        label='Pastoralna bilješka',
        required=False,
        widget=forms.Textarea(attrs={'rows': 5, **_WIDGET}),
    )


class StreetForm(forms.Form):
    name = forms.CharField(label='Ulica', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    city = forms.CharField(label='Grad', max_length=120, required=False, widget=forms.TextInput(attrs=_WIDGET))
    notes = forms.CharField(label='Napomena', required=False, widget=forms.Textarea(attrs={'rows': 2, **_WIDGET}))

class VisitForm(forms.Form):
    scheduled = forms.DateField(
        label='Datum posjeta',
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    person = forms.CharField(
        label='Osoba',
        max_length=120,
        widget=forms.TextInput(attrs={
            **_WIDGET,
            'autocomplete': 'off',
            'role': 'combobox',
            'aria-autocomplete': 'list',
            'aria-expanded': 'false',
            'data-visit-person-search': '',
            'aria-controls': 'visit-person-list',
            'placeholder': 'Pretraži osobu ili obitelj',
        }),
    )
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
    address = forms.CharField(
        label='Adresa',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'data-visit-address': ''}),
    )
    family_id = forms.CharField(
        required=False,
        max_length=40,
        widget=forms.HiddenInput(attrs={'data-visit-family-id': ''}),
    )
    report = forms.CharField(
        label='Napomena',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, **_WIDGET}),
    )

