"""Obrasci za matične knjige i isprave."""
from django import forms

_WIDGET = {'class': 'form-control'}


class RegistryBookForm(forms.Form):
    title = forms.CharField(label='Naziv knjige', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    book_type = forms.ChoiceField(
        label='Vrsta',
        choices=[
            ('krštenja', 'Rođeni i kršteni'),
            ('vjenčanja', 'Vjenčanja'),
            ('umrli', 'Umrli'),
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


class BaptismRegistryForm(forms.Form):
    """Službeni upis u maticu rođenih i krštenih."""

    CHILD_SEX_CHOICES = (('', 'Odaberite…'), ('son', 'Sin'), ('daughter', 'Kći'))
    IDENTIFIER_TYPE_CHOICES = (('', '—'), ('oib', 'OIB'), ('jmbg', 'JMBG'))
    YES_NO_CHOICES = ((True, 'Da'), (False, 'Ne'))

    entry_number = forms.IntegerField(
        label='Redni broj', min_value=1, required=False,
        widget=forms.NumberInput(attrs={**_WIDGET, 'readonly': True, 'placeholder': 'Dodjeljuje se automatski'}),
    )
    birth_date = forms.DateField(label='Datum rođenja', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    baptism_date = forms.DateField(label='Datum krštenja', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    child_first_name = forms.CharField(label='Ime djeteta', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    child_last_name = forms.CharField(label='Prezime djeteta', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    child_sex = forms.ChoiceField(label='Sin ili kći', choices=CHILD_SEX_CHOICES, widget=forms.Select(attrs=_WIDGET))
    baptism_place = forms.CharField(label='Mjesto krštenja', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    identifier_type = forms.ChoiceField(label='Vrsta identifikatora', choices=IDENTIFIER_TYPE_CHOICES, required=False, widget=forms.Select(attrs=_WIDGET))
    identifier_value = forms.CharField(label='JMBG / OIB', max_length=13, required=False, widget=forms.TextInput(attrs={**_WIDGET, 'inputmode': 'numeric'}))
    father_first_name = forms.CharField(label='Ime oca', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    father_last_name = forms.CharField(label='Prezime oca', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    father_religion = forms.CharField(label='Vjera oca', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    mother_first_name = forms.CharField(label='Ime majke', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    mother_last_name = forms.CharField(label='Djevojačko prezime majke', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    mother_religion = forms.CharField(label='Vjera majke', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    parents_canonically_married = forms.TypedChoiceField(
        label='Roditelji kanonski vjenčani', choices=YES_NO_CHOICES,
        coerce=lambda value: value == 'True', initial=True,
        widget=forms.Select(attrs=_WIDGET),
    )
    residence_address = forms.CharField(label='Adresa prebivališta', max_length=255, widget=forms.TextInput(attrs=_WIDGET))
    godparent_first_name = forms.CharField(label='Ime kuma / kume', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    godparent_last_name = forms.CharField(label='Prezime kuma / kume', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    minister_first_name = forms.CharField(label='Ime krstitelja', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    minister_last_name = forms.CharField(label='Prezime krstitelja', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    minister_role = forms.CharField(label='Služba krstitelja', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    confirmation_date = forms.DateField(label='Datum potvrde', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    confirmation_place = forms.CharField(label='Mjesto potvrde', max_length=200, required=False, widget=forms.TextInput(attrs=_WIDGET))
    confirmation_parish = forms.CharField(label='Župa potvrde', max_length=200, required=False, widget=forms.TextInput(attrs=_WIDGET))
    marriage_date = forms.DateField(label='Datum ženidbe', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    marriage_parish = forms.CharField(label='Župa ženidbe', max_length=200, required=False, widget=forms.TextInput(attrs=_WIDGET))
    spouse_first_name = forms.CharField(label='Ime supružnika', max_length=160, required=False, widget=forms.TextInput(attrs=_WIDGET))
    spouse_last_name = forms.CharField(label='Prezime supružnika', max_length=160, required=False, widget=forms.TextInput(attrs=_WIDGET))
    notes = forms.CharField(label='Naknadni upisi i bilješke', required=False, widget=forms.Textarea(attrs={**_WIDGET, 'rows': 3}))
    physical_page = forms.CharField(label='Stranica u fizičkoj matici', max_length=40, required=False, widget=forms.TextInput(attrs=_WIDGET))

    def __init__(self, *args, selected_year: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['baptism_date'].widget.attrs.update({
            'min': f'{selected_year:04d}-01-01',
            'max': f'{selected_year:04d}-12-31',
        })

    def clean(self):
        cleaned_data = super().clean()
        birth_date = cleaned_data.get('birth_date')
        baptism_date = cleaned_data.get('baptism_date')
        if birth_date and baptism_date and birth_date > baptism_date:
            self.add_error('baptism_date', 'Datum krštenja ne može biti prije datuma rođenja.')
        identifier_type = cleaned_data.get('identifier_type')
        identifier_value = (cleaned_data.get('identifier_value') or '').strip()
        if bool(identifier_type) != bool(identifier_value):
            self.add_error('identifier_value', 'Vrsta i vrijednost identifikatora unose se zajedno.')
        elif identifier_type == 'oib' and (len(identifier_value) != 11 or not identifier_value.isdigit()):
            self.add_error('identifier_value', 'OIB mora sadržavati 11 znamenki.')
        elif identifier_type == 'jmbg' and (len(identifier_value) != 13 or not identifier_value.isdigit()):
            self.add_error('identifier_value', 'JMBG mora sadržavati 13 znamenki.')
        return cleaned_data


def baptism_registry_initial(record: dict) -> dict:
    def split_name(value):
        parts = str(value or '').strip().split()
        return (' '.join(parts[:-1]), parts[-1]) if len(parts) > 1 else ((parts[0] if parts else ''), '')

    child = split_name(record.get('childName'))
    godparent = split_name(record.get('godparents'))
    minister = split_name(record.get('celebrant'))
    parents = str(record.get('parents') or '').split('/', maxsplit=1)
    father = split_name(parents[0])
    mother = split_name(parents[1] if len(parents) > 1 else '')
    entry_number = record.get('entryNumber')
    if not entry_number:
        registry_number = str(record.get('registryNo') or '')
        entry_number = (
            registry_number.rsplit('/', maxsplit=1)[-1]
            if registry_number.rsplit('/', maxsplit=1)[-1].isdigit()
            else None
        )
    return {
        'entry_number': entry_number,
        'birth_date': record.get('birthDate'), 'baptism_date': record.get('baptismDate'),
        'child_first_name': record.get('childFirstName') or child[0],
        'child_last_name': record.get('childLastName') or child[1],
        'child_sex': record.get('childSex') or '', 'baptism_place': record.get('baptismPlace', ''),
        'identifier_type': record.get('identifierType', ''), 'identifier_value': record.get('identifierValue', ''),
        'father_first_name': record.get('fatherFirstName') or father[0], 'father_last_name': record.get('fatherLastName') or father[1],
        'father_religion': record.get('fatherReligion', ''), 'mother_first_name': record.get('motherFirstName') or mother[0],
        'mother_last_name': record.get('motherLastName') or mother[1], 'mother_religion': record.get('motherReligion', ''),
        'parents_canonically_married': record.get('parentsCanonicallyMarried', True),
        'residence_address': record.get('residenceAddress', ''),
        'godparent_first_name': record.get('godparentFirstName') or godparent[0],
        'godparent_last_name': record.get('godparentLastName') or godparent[1],
        'minister_first_name': record.get('ministerFirstName') or minister[0],
        'minister_last_name': record.get('ministerLastName') or minister[1],
        'minister_role': record.get('ministerRole', ''), 'confirmation_date': record.get('confirmationDate'),
        'confirmation_place': record.get('confirmationPlace'), 'confirmation_parish': record.get('confirmationParish'),
        'marriage_date': record.get('marriageDate'), 'marriage_parish': record.get('marriageParish'),
        'spouse_first_name': record.get('spouseFirstName'), 'spouse_last_name': record.get('spouseLastName'),
        'notes': record.get('notes'), 'physical_page': record.get('physicalPage'),
    }


class MarriageRegistryForm(forms.Form):
    entry_number = forms.IntegerField(label='Redni broj', min_value=1, required=False, widget=forms.NumberInput(attrs={**_WIDGET, 'readonly': True, 'placeholder': 'Dodjeljuje se automatski'}))
    physical_page = forms.CharField(label='Stranica u fizičkoj knjizi', max_length=40, required=False, widget=forms.TextInput(attrs=_WIDGET))
    marriage_date = forms.DateField(label='Datum vjenčanja', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    marriage_place = forms.CharField(label='Mjesto vjenčanja', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    groom_first_name = forms.CharField(label='Ime zaručnika', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    groom_last_name = forms.CharField(label='Prezime zaručnika', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    groom_birth_place = forms.CharField(label='Mjesto rođenja zaručnika', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    groom_birth_date = forms.DateField(label='Datum rođenja zaručnika', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    groom_oib = forms.CharField(label='OIB zaručnika', max_length=11, required=False, widget=forms.TextInput(attrs={**_WIDGET, 'inputmode': 'numeric'}))
    groom_religion = forms.CharField(label='Vjera zaručnika', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    groom_baptism_date = forms.DateField(label='Datum krštenja zaručnika', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    groom_baptism_parish = forms.CharField(label='Župa krštenja zaručnika', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    groom_baptism_parish_address = forms.CharField(label='Adresa župe krštenja zaručnika', max_length=255, widget=forms.TextInput(attrs=_WIDGET))
    groom_residence_address = forms.CharField(label='Adresa prebivališta zaručnika', max_length=255, widget=forms.TextInput(attrs=_WIDGET))
    bride_first_name = forms.CharField(label='Ime zaručnice', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    bride_last_name = forms.CharField(label='Prezime zaručnice', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    bride_birth_place = forms.CharField(label='Mjesto rođenja zaručnice', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    bride_birth_date = forms.DateField(label='Datum rođenja zaručnice', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    bride_oib = forms.CharField(label='OIB zaručnice', max_length=11, required=False, widget=forms.TextInput(attrs={**_WIDGET, 'inputmode': 'numeric'}))
    bride_religion = forms.CharField(label='Vjera zaručnice', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    bride_baptism_date = forms.DateField(label='Datum krštenja zaručnice', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    bride_baptism_parish = forms.CharField(label='Župa krštenja zaručnice', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    bride_baptism_parish_address = forms.CharField(label='Adresa župe krštenja zaručnice', max_length=255, widget=forms.TextInput(attrs=_WIDGET))
    bride_residence_address = forms.CharField(label='Adresa prebivališta zaručnice', max_length=255, widget=forms.TextInput(attrs=_WIDGET))
    groom_father_first_name = forms.CharField(label='Ime oca zaručnika', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    groom_father_last_name = forms.CharField(label='Prezime oca zaručnika', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    groom_mother_first_name = forms.CharField(label='Ime majke zaručnika', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    groom_mother_maiden_name = forms.CharField(label='Djevojačko prezime majke zaručnika', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    bride_father_first_name = forms.CharField(label='Ime oca zaručnice', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    bride_father_last_name = forms.CharField(label='Prezime oca zaručnice', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    bride_mother_first_name = forms.CharField(label='Ime majke zaručnice', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    bride_mother_maiden_name = forms.CharField(label='Djevojačko prezime majke zaručnice', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    groom_witness_first_name = forms.CharField(label='Ime svjedoka zaručnika', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    groom_witness_last_name = forms.CharField(label='Prezime svjedoka zaručnika', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    bride_witness_first_name = forms.CharField(label='Ime svjedoka zaručnice', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    bride_witness_last_name = forms.CharField(label='Prezime svjedoka zaručnice', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    officiant_first_name = forms.CharField(label='Ime vjenčatelja', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    officiant_last_name = forms.CharField(label='Prezime vjenčatelja', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    officiant_role = forms.CharField(label='Služba vjenčatelja', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    notes = forms.CharField(label='Napomene', required=False, help_text='Ovdje evidentirajte ženidbene navještaje, dopuštenja, dispenze i ostale napomene.', widget=forms.Textarea(attrs={**_WIDGET, 'rows': 3}))

    def __init__(self, *args, selected_year: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['marriage_date'].widget.attrs.update({'min': f'{selected_year:04d}-01-01', 'max': f'{selected_year:04d}-12-31'})

    def clean(self):
        cleaned = super().clean()
        marriage_date = cleaned.get('marriage_date')
        for side, label in (('groom', 'zaručnika'), ('bride', 'zaručnice')):
            birth_date = cleaned.get(f'{side}_birth_date')
            baptism_date = cleaned.get(f'{side}_baptism_date')
            if birth_date and baptism_date and birth_date > baptism_date:
                self.add_error(f'{side}_baptism_date', f'Datum krštenja {label} ne može biti prije datuma rođenja.')
            if baptism_date and marriage_date and baptism_date > marriage_date:
                self.add_error(f'{side}_baptism_date', f'Datum krštenja {label} ne može biti nakon vjenčanja.')
            oib = (cleaned.get(f'{side}_oib') or '').strip()
            if oib and (len(oib) != 11 or not oib.isdigit()):
                self.add_error(f'{side}_oib', 'OIB mora sadržavati 11 znamenki.')
        return cleaned


def marriage_registry_initial(record: dict) -> dict:
    return {
        'entry_number': record.get('entryNumber'), 'physical_page': record.get('physicalPage'),
        'marriage_date': record.get('weddingDate'), 'marriage_place': record.get('marriagePlace') or record.get('church'),
        'groom_first_name': record.get('groomFirstName'), 'groom_last_name': record.get('groomLastName'),
        'groom_birth_place': record.get('groomBirthPlace'), 'groom_birth_date': record.get('groomBirthDate'), 'groom_oib': record.get('groomOib'),
        'groom_religion': record.get('groomReligion'), 'groom_baptism_date': record.get('groomBaptismDate'),
        'groom_baptism_parish': record.get('groomBaptismParish'), 'groom_baptism_parish_address': record.get('groomBaptismParishAddress'), 'groom_residence_address': record.get('groomResidenceAddress'),
        'bride_first_name': record.get('brideFirstName'), 'bride_last_name': record.get('brideLastName'),
        'bride_birth_place': record.get('brideBirthPlace'), 'bride_birth_date': record.get('brideBirthDate'), 'bride_oib': record.get('brideOib'),
        'bride_religion': record.get('brideReligion'), 'bride_baptism_date': record.get('brideBaptismDate'),
        'bride_baptism_parish': record.get('brideBaptismParish'), 'bride_baptism_parish_address': record.get('brideBaptismParishAddress'), 'bride_residence_address': record.get('brideResidenceAddress'),
        'groom_father_first_name': record.get('groomFatherFirstName'), 'groom_father_last_name': record.get('groomFatherLastName'),
        'groom_mother_first_name': record.get('groomMotherFirstName'), 'groom_mother_maiden_name': record.get('groomMotherMaidenName'),
        'bride_father_first_name': record.get('brideFatherFirstName'), 'bride_father_last_name': record.get('brideFatherLastName'),
        'bride_mother_first_name': record.get('brideMotherFirstName'), 'bride_mother_maiden_name': record.get('brideMotherMaidenName'),
        'groom_witness_first_name': record.get('groomWitnessFirstName'), 'groom_witness_last_name': record.get('groomWitnessLastName'),
        'bride_witness_first_name': record.get('brideWitnessFirstName'), 'bride_witness_last_name': record.get('brideWitnessLastName'),
        'officiant_first_name': record.get('officiantFirstName'), 'officiant_last_name': record.get('officiantLastName'), 'officiant_role': record.get('officiantRole'),
        'notes': record.get('notes'),
    }


class FuneralRegistryForm(forms.Form):
    SEX_CHOICES = (('', 'Odaberite…'), ('male', 'Muško'), ('female', 'Žensko'))
    IDENTIFIER_TYPE_CHOICES = (('', '—'), ('oib', 'OIB'), ('jmbg', 'JMBG'))

    entry_number = forms.IntegerField(label='Redni broj', min_value=1, required=False, widget=forms.NumberInput(attrs={**_WIDGET, 'readonly': True, 'placeholder': 'Dodjeljuje se automatski'}))
    physical_page = forms.CharField(label='Stranica u fizičkoj knjizi', max_length=40, required=False, widget=forms.TextInput(attrs=_WIDGET))
    death_date = forms.DateField(label='Datum smrti', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    death_place = forms.CharField(label='Mjesto smrti', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    first_name = forms.CharField(label='Ime osobe', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    last_name = forms.CharField(label='Prezime osobe', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    sex = forms.ChoiceField(label='Spol', choices=SEX_CHOICES, widget=forms.Select(attrs=_WIDGET))
    birth_place = forms.CharField(label='Mjesto rođenja', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    birth_date = forms.DateField(label='Datum rođenja', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    identifier_type = forms.ChoiceField(label='Vrsta identifikatora', choices=IDENTIFIER_TYPE_CHOICES, required=False, widget=forms.Select(attrs=_WIDGET))
    identifier_value = forms.CharField(label='JMBG / OIB', max_length=13, required=False, widget=forms.TextInput(attrs={**_WIDGET, 'inputmode': 'numeric'}))
    spouse_first_name = forms.CharField(label='Ime supružnika', max_length=160, required=False, widget=forms.TextInput(attrs=_WIDGET))
    spouse_last_name = forms.CharField(label='Prezime supružnika', max_length=160, required=False, widget=forms.TextInput(attrs=_WIDGET))
    father_first_name = forms.CharField(label='Ime oca', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    father_last_name = forms.CharField(label='Prezime oca', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    mother_first_name = forms.CharField(label='Ime majke', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    mother_last_name = forms.CharField(label='Prezime majke', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    residence_address = forms.CharField(label='Adresa prebivališta', max_length=255, widget=forms.TextInput(attrs=_WIDGET))
    received_confession = forms.BooleanField(label='Ispovijed', required=False)
    received_anointing = forms.BooleanField(label='Bolesničko pomazanje', required=False)
    received_communion = forms.BooleanField(label='Pričest', required=False)
    burial_place = forms.CharField(label='Mjesto pokopa', max_length=240, widget=forms.TextInput(attrs=_WIDGET))
    burial_date = forms.DateField(label='Datum pokopa', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    minister_first_name = forms.CharField(label='Ime crkvenog službenika', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    minister_last_name = forms.CharField(label='Prezime crkvenog službenika', max_length=160, widget=forms.TextInput(attrs=_WIDGET))
    cause_of_death = forms.CharField(label='Uzrok smrti', max_length=255, required=False, widget=forms.TextInput(attrs=_WIDGET))
    notes = forms.CharField(label='Bilješke', required=False, widget=forms.Textarea(attrs={**_WIDGET, 'rows': 3}))

    def __init__(self, *args, selected_year: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['death_date'].widget.attrs.update({'min': f'{selected_year:04d}-01-01', 'max': f'{selected_year:04d}-12-31'})

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('birth_date') and cleaned.get('death_date') and cleaned['birth_date'] > cleaned['death_date']:
            self.add_error('death_date', 'Datum smrti ne može biti prije datuma rođenja.')
        if cleaned.get('burial_date') and cleaned.get('death_date') and cleaned['burial_date'] < cleaned['death_date']:
            self.add_error('burial_date', 'Datum pokopa ne može biti prije datuma smrti.')
        kind, value = cleaned.get('identifier_type'), (cleaned.get('identifier_value') or '').strip()
        if bool(kind) != bool(value):
            self.add_error('identifier_value', 'Vrsta i vrijednost identifikatora unose se zajedno.')
        elif kind == 'oib' and (len(value) != 11 or not value.isdigit()):
            self.add_error('identifier_value', 'OIB mora sadržavati 11 znamenki.')
        elif kind == 'jmbg' and (len(value) != 13 or not value.isdigit()):
            self.add_error('identifier_value', 'JMBG mora sadržavati 13 znamenki.')
        return cleaned


def funeral_registry_initial(record: dict) -> dict:
    def split_name(value):
        parts = str(value or '').strip().split()
        return (' '.join(parts[:-1]), parts[-1]) if len(parts) > 1 else ((parts[0] if parts else ''), '')
    deceased = split_name(record.get('deceased'))
    minister = split_name(record.get('celebrant'))
    reference = str(record.get('registryNo') or '')
    entry_number = record.get('entryNumber') or (reference.rsplit('/', 1)[-1] if reference.rsplit('/', 1)[-1].isdigit() else None)
    return {
        'entry_number': entry_number, 'physical_page': record.get('physicalPage'),
        'death_date': record.get('deathDate'), 'death_place': record.get('deathPlace'),
        'first_name': record.get('firstName') or deceased[0], 'last_name': record.get('lastName') or deceased[1],
        'sex': record.get('sex') or '', 'birth_place': record.get('birthPlace'), 'birth_date': record.get('birthDate'),
        'identifier_type': record.get('identifierType'), 'identifier_value': record.get('identifierValue'),
        'spouse_first_name': record.get('spouseFirstName'), 'spouse_last_name': record.get('spouseLastName'),
        'father_first_name': record.get('fatherFirstName'), 'father_last_name': record.get('fatherLastName'),
        'mother_first_name': record.get('motherFirstName'), 'mother_last_name': record.get('motherLastName'),
        'residence_address': record.get('residenceAddress'), 'received_confession': record.get('receivedConfession', False),
        'received_anointing': record.get('receivedAnointing', False), 'received_communion': record.get('receivedCommunion', False),
        'burial_place': record.get('burialPlace') or record.get('cemetery'), 'burial_date': record.get('burialDate') or record.get('funeralDate'),
        'minister_first_name': record.get('ministerFirstName') or minister[0], 'minister_last_name': record.get('ministerLastName') or minister[1],
        'cause_of_death': record.get('causeOfDeath'), 'notes': record.get('notes'),
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


