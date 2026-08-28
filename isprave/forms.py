"""Obrasci za matične knjige i isprave."""
from django import forms

_WIDGET = {'class': 'form-control'}


class RegistryBookForm(forms.Form):
    title = forms.CharField(label='Naziv knjige', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    book_type = forms.ChoiceField(
        label='Vrsta',
        choices=[
            ('krštenja', 'Krštenja'),
            ('vjenčanja', 'Vjenčanja'),
            ('umrli', 'Umrli'),
            ('krizma', 'Krizma'),
            ('ostalo', 'Ostalo'),
        ],
        widget=forms.Select(attrs=_WIDGET),
    )
    location = forms.CharField(label='Lokacija', max_length=120, required=False, widget=forms.TextInput(attrs=_WIDGET))
    last_entry = forms.DateField(label='Zadnji unos', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    last_no = forms.CharField(label='Zadnji broj', max_length=40, required=False, widget=forms.TextInput(attrs=_WIDGET))
    custodian = forms.CharField(label='Skrbnik', max_length=100, required=False, widget=forms.TextInput(attrs=_WIDGET))
    status = forms.CharField(label='Status', max_length=60, required=False, initial='u župi', widget=forms.TextInput(attrs=_WIDGET))
    notes = forms.CharField(label='Napomena', required=False, widget=forms.Textarea(attrs={'rows': 2, **_WIDGET}))


REGISTRY_RECORD_FIELD_CONFIGURATION = {
    'krštenja': {
        'labels': {
            'subject_name': 'Krštenik',
            'record_date': 'Datum krštenja',
            'related_people': 'Roditelji',
            'sponsors': 'Kumovi',
        },
        'hidden_fields': {'baptism_date', 'place'},
    },
    'vjenčanja': {
        'labels': {
            'subject_name': 'Mladenci',
            'record_date': 'Datum vjenčanja',
            'related_people': 'Svjedoci',
            'place': 'Crkva',
        },
        'hidden_fields': {'birth_date', 'baptism_date', 'sponsors'},
    },
    'umrli': {
        'labels': {
            'subject_name': 'Pokojnik',
            'record_date': 'Datum sprovoda',
            'birth_date': 'Datum smrti',
            'place': 'Groblje',
        },
        'hidden_fields': {'baptism_date', 'related_people', 'sponsors'},
    },
    'krizma': {
        'labels': {
            'subject_name': 'Krizmanik',
            'record_date': 'Datum krizme',
            'sponsors': 'Kum/ka',
            'celebrant': 'Biskup / slavitelj',
        },
        'hidden_fields': {'related_people', 'place'},
    },
    'ostalo': {
        'labels': {
            'subject_name': 'Naziv zapisa / osoba',
            'record_date': 'Datum zapisa',
            'place': 'Mjesto / napomena',
        },
        'hidden_fields': {
            'birth_date',
            'baptism_date',
            'related_people',
            'sponsors',
        },
    },
}


class RegistryRecordForm(forms.Form):
    registry_number = forms.CharField(
        label='Redni broj (dodjeljuje se automatski)',
        max_length=60,
        required=False,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    subject_name = forms.CharField(
        label='Osoba / zapis',
        max_length=200,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    record_date = forms.DateField(
        label='Datum zapisa',
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    birth_date = forms.DateField(
        label='Datum rođenja',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    baptism_date = forms.DateField(
        label='Datum krštenja',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    related_people = forms.CharField(
        label='Povezane osobe',
        max_length=240,
        required=False,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    sponsors = forms.CharField(
        label='Kumovi / svjedoci',
        max_length=240,
        required=False,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    place = forms.CharField(
        label='Mjesto',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    celebrant = forms.CharField(
        label='Slavitelj',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    status = forms.CharField(
        label='Status',
        max_length=60,
        required=False,
        initial='upisano',
        widget=forms.TextInput(attrs=_WIDGET),
    )

    def __init__(
        self,
        *args,
        registry_type: str,
        selected_year: int,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        field_configuration = REGISTRY_RECORD_FIELD_CONFIGURATION.get(
            registry_type,
            {'labels': {}, 'hidden_fields': set()},
        )
        for field_name in field_configuration['hidden_fields']:
            self.fields.pop(field_name, None)
        for field_name, field_label in field_configuration['labels'].items():
            if field_name in self.fields:
                self.fields[field_name].label = field_label

        self.fields['registry_number'].widget.attrs.update({
            'readonly': True,
            'placeholder': 'Dodjeljuje se nakon spremanja',
        })

        first_date_of_year = f'{selected_year:04d}-01-01'
        last_date_of_year = f'{selected_year:04d}-12-31'
        self.fields['record_date'].widget.attrs.update({
            'min': first_date_of_year,
            'max': last_date_of_year,
        })


