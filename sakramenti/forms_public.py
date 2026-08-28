"""Javni obrasci za sakramentalne prijave."""
from collections import OrderedDict
from datetime import date

from django import forms

_WIDGET = {'class': 'form-control'}

LEGAL_CONSENT_FIELDS = ('privacy_consent', 'terms_consent', 'gdpr_consent')
PRIVACY_NOTICE_VERSION = '2026-08'
TERMS_VERSION = '2026-08'

STREET_NOT_LISTED = '__other__'

_DATE = forms.DateInput(attrs={'type': 'date', **_WIDGET})
_TIME = forms.TimeInput(attrs={'type': 'time', **_WIDGET})
_TEXTAREA = forms.Textarea(attrs={'rows': 3, **_WIDGET})

_YES_NO = (('da', 'Da'), ('ne', 'Ne'))
_SPOL = (('', '— Odaberite —'), ('m', 'Muški'), ('z', 'Ženski'))
_VJEROISPOVIJEST = (
    ('', '— Odaberite —'),
    ('katolicka', 'Katolička'),
    ('pravoslavna', 'Pravoslavna'),
    ('protestantska', 'Protestantska'),
    ('druga_krscanska', 'Druga kršćanska'),
    ('neciscanska', 'Nekršćanska ili bez ispovijesti'),
)
_VJENCANI_STATUS = (
    ('', '— Odaberite —'),
    ('crkveni_brak', 'U crkvenom braku'),
    ('civilni_brak', 'Samo građanski brak'),
    ('izvan_braka', 'Nisu u braku'),
    ('udovistvo', 'Udovištvo'),
    ('ostalo', 'Ostalo'),
)


def compose_baptism_child_name(data: dict) -> str:
    return ' '.join(
        part for part in (
            str(data.get('ime') or '').strip(),
            str(data.get('prezime') or '').strip(),
        ) if part
    ) or str(data.get('ime_djeteta') or '').strip()


def compose_baptism_parents_line(data: dict) -> str:
    parts = []
    if str(data.get('otac_poznat') or 'da') != 'ne':
        father = ' '.join(part for part in (
            str(data.get('otac_ime') or '').strip(),
            str(data.get('otac_prezime') or '').strip(),
        ) if part)
        if father:
            parts.append(father)
    if str(data.get('majka_poznata') or 'da') != 'ne':
        mother = ' '.join(part for part in (
            str(data.get('majka_ime') or '').strip(),
            str(data.get('majka_prezime') or '').strip(),
        ) if part)
        maiden = str(data.get('majka_djevojacko') or '').strip()
        if mother and maiden:
            mother = f'{mother} (r. {maiden})'
        if mother:
            parts.append(mother)
    return ' i '.join(parts) or str(data.get('roditelji') or '').strip()


def compose_baptism_godparents_line(data: dict) -> str:
    names = []
    for prefix in ('kum1', 'kum2'):
        name = ' '.join(part for part in (
            str(data.get(f'{prefix}_ime') or '').strip(),
            str(data.get(f'{prefix}_prezime') or '').strip(),
        ) if part)
        if name:
            names.append(name)
    return ', '.join(names) or str(
        data.get('kumovi') or data.get('kum') or ''
    ).strip()


def pastoral_year_choices(today=None):
    today = today or date.today()
    start = today.year if today.month >= 9 else today.year - 1
    years = ((start - 1, start), (start, start + 1), (start + 1, start + 2))
    return tuple(
        (f'{begin}/{end}', f'Pastoralna godina {begin}/{end}')
        for begin, end in years
    )


def pastoral_year_end(value) -> int | None:
    text = str(value or '')
    if '/' not in text:
        return None
    try:
        return int(text.split('/')[-1])
    except ValueError:
        return None


def compose_sponsor_name(data: dict) -> str:
    name = ' '.join(part for part in (
        str(data.get('kum_ime') or '').strip(),
        str(data.get('kum_prezime') or '').strip(),
    ) if part)
    return name or str(data.get('kum') or '').strip()


def compose_school_class(data: dict) -> str:
    number = str(data.get('razred_broj') or '').strip()
    letter = str(data.get('razred_slovo') or '').strip()
    if number == 'zavrseno':
        return 'Škola je završena'
    return ' '.join(part for part in (number, letter) if part) or str(
        data.get('razred') or ''
    ).strip()


def compose_person_name(*parts) -> str:
    return ' '.join(
        str(part or '').strip() for part in parts if str(part or '').strip()
    )


def compose_couple_name(data: dict) -> str:
    groom = compose_person_name(
        data.get('zarucnik_ime'), data.get('zarucnik_prezime'),
    )
    bride = compose_person_name(
        data.get('zarucnica_ime'),
        data.get('zarucnica_civilno_prezime')
        or data.get('zarucnica_rodjeno_prezime'),
    )
    if groom and bride:
        return f'{groom} i {bride}'
    return groom or bride or str(data.get('par') or '').strip()


def compose_wedding_witnesses_line(data: dict) -> str:
    names = []
    for prefix in ('svjedok1', 'svjedok2'):
        name = compose_person_name(
            data.get(f'{prefix}_ime'), data.get(f'{prefix}_prezime'),
        )
        if name:
            names.append(name)
    return ', '.join(names) or str(data.get('kumovi') or '').strip()


class PublicFormBase(forms.Form):
    privacy_consent = forms.BooleanField(
        label='Prihvaćam Politiku privatnosti.',
        required=True,
    )
    terms_consent = forms.BooleanField(
        label='Prihvaćam Opće uvjete korištenja.',
        required=True,
    )
    gdpr_consent = forms.BooleanField(
        label='Dajem privolu za obradu osobnih podataka u svrhu ove pastoralne prijave.',
        required=True,
    )

    def __init__(self, *args, streets=None, parish_email='', parish_phone='', **kwargs):
        self._streets = streets or []
        self._street_map = {s['id']: s for s in self._streets}
        self._parish_email = parish_email
        self._parish_phone = parish_phone
        super().__init__(*args, **kwargs)
        self._init_street_field()
        self._reorder_address_fields()

    def _reorder_address_fields(self):
        tail = ('street_id', 'house_number') + LEGAL_CONSENT_FIELDS
        ordered = OrderedDict()
        for key, field in self.fields.items():
            if key not in tail:
                ordered[key] = field
        for key in tail:
            if key in self.fields:
                ordered[key] = self.fields[key]
        self.fields = ordered

    def _init_street_field(self):
        choices = [('', '— Odaberite ulicu —')]
        for street in sorted(self._streets, key=lambda s: (s.get('sortOrder', 0), s.get('name', ''))):
            zone = street.get('zone', '')
            label = street.get('name', '')
            if zone:
                label = f'{label} ({zone})'
            choices.append((street['id'], label))
        choices.append((STREET_NOT_LISTED, 'Moje adrese nema na popisu'))
        self.fields['street_id'] = forms.ChoiceField(
            label='Ulica',
            choices=choices,
            required=True,
            widget=forms.Select(attrs={**_WIDGET, 'id': 'street-select'}),
        )
        self.fields['house_number'] = forms.CharField(
            label='Kućni broj',
            max_length=30,
            required=True,
            widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'npr. 12'}),
        )

    def _address_not_found_message(self) -> str:
        parts = ['Ako ne možete pronaći svoju adresu na popisu, molimo obratite se župnom uredu']
        if self._parish_email:
            parts.append(f'putem e-pošte ({self._parish_email})')
        if self._parish_phone:
            parts.append(f'ili telefonom ({self._parish_phone})')
        parts.append('ili osobnim dolaskom u ured.')
        return ' '.join(parts) + ' Prijava putem obrasca nije moguća bez adrese s popisa.'

    def clean(self):
        cleaned = super().clean()
        street_id = cleaned.get('street_id')
        if street_id == STREET_NOT_LISTED:
            self.add_error('street_id', self._address_not_found_message())
        elif street_id and street_id not in self._street_map:
            self.add_error('street_id', 'Odabrana ulica nije valjana.')
        return cleaned

    def resolved_address(self) -> str:
        street_id = self.cleaned_data.get('street_id')
        house = self.cleaned_data.get('house_number', '').strip()
        street = self._street_map.get(street_id, {})
        name = street.get('name', '')
        if name and house:
            return f'{name} {house}'
        return name or house


class PublicWizardForm(PublicFormBase):
    STEPS = ()
    FIELD_STEPS = {}
    STEP_INTROS = {}
    WIZARD_NOTICES = ()
    ADDRESS_STEP = ''

    def _reorder_address_fields(self):
        if self.FIELD_STEPS:
            self._reorder_fields_by_step()
            return
        super()._reorder_address_fields()

    def _reorder_fields_by_step(self):
        ordered = OrderedDict()
        for name in self.FIELD_STEPS:
            if name in self.fields:
                ordered[name] = self.fields[name]
        for name, field in self.fields.items():
            if name not in ordered:
                ordered[name] = field
        self.fields = ordered

    def fields_for_step(self, step_id: str):
        return [
            self[name]
            for name, field_step in self.FIELD_STEPS.items()
            if field_step == step_id and name in self.fields and name not in LEGAL_CONSENT_FIELDS
        ]


class KrizmaPublicForm(PublicWizardForm):
    STEPS = (
        ('prijava', 'Prijava'),
        ('krizmanik', 'Krizmanik'),
        ('sakramenti', 'Sakramenti'),
        ('obitelj', 'Roditelji / kum'),
    )
    FIELD_STEPS = {
        'pastoralna_godina': 'prijava',
        'podnositelj': 'prijava',
        'email': 'prijava',
        'ime': 'krizmanik',
        'prezime': 'krizmanik',
        'spol': 'krizmanik',
        'datum_rodjenja': 'krizmanik',
        'mjesto_rodjenja': 'krizmanik',
        'street_id': 'krizmanik',
        'house_number': 'krizmanik',
        'zupa_stanovanja': 'krizmanik',
        'djetetov_email': 'krizmanik',
        'djetetov_telefon': 'krizmanik',
        'skola': 'krizmanik',
        'razred_broj': 'krizmanik',
        'razred_slovo': 'krizmanik',
        'vjeronauk': 'krizmanik',
        'vjeroucitelj': 'krizmanik',
        'datum_krstenja': 'sakramenti',
        'zupa_krstenja': 'sakramenti',
        'zupa_pricesti': 'sakramenti',
        'otac_ime': 'obitelj',
        'otac_prezime': 'obitelj',
        'otac_telefon': 'obitelj',
        'otac_email': 'obitelj',
        'majka_ime': 'obitelj',
        'majka_prezime': 'obitelj',
        'majka_djevojacko': 'obitelj',
        'majka_telefon': 'obitelj',
        'majka_email': 'obitelj',
        'kum_ime': 'obitelj',
        'kum_prezime': 'obitelj',
        'kum_spol': 'obitelj',
        'kum_telefon': 'obitelj',
        'kum_email': 'obitelj',
        'napomena': 'obitelj',
        'gdpr_consent': 'obitelj',
    }
    ADDRESS_STEP = 'krizmanik'
    WIZARD_NOTICES = (
        (
            'alert',
            'Prijava je za pripremu sakramenta krizme u tekućoj ili sljedećoj pastoralnoj godini. Ako je krizmanik maloljetan, obrazac ispunjava roditelj ili skrbnik.',
        ),
        (
            'note',
            'Pri unosu imena pazite na dijakritike (č, ć, đ, š, ž). Kontakt barem jednog roditelja (telefon i e-mail) je obavezan.',
        ),
    )
    STEP_INTROS = {
        'prijava': 'Odaberite pastoralnu godinu te unesite tko podnosi zahtjev i e-mail za obavijesti.',
        'krizmanik': 'Osobni podaci, adresa, škola i vjeronauk.',
        'sakramenti': 'Datum i župa krštenja te župa prve pričesti, ako nisu u ovoj župi.',
        'obitelj': 'Podaci o roditeljima. Kuma unesite ako je već poznat.',
    }

    gdpr_consent = forms.BooleanField(
        label='Dajem privolu za obradu osobnih podataka u svrhu prijave i upisa krizmanika.',
        required=True,
    )
    pastoralna_godina = forms.ChoiceField(
        label='Krizma će biti',
        choices=pastoral_year_choices(),
        widget=forms.Select(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    podnositelj = forms.CharField(
        label='Podnositelj zahtjeva',
        max_length=120,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    email = forms.EmailField(
        label='E-mail za obavijesti',
        widget=forms.EmailInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    ime = forms.CharField(label='Ime krizmanika', max_length=100)
    prezime = forms.CharField(label='Prezime krizmanika', max_length=100)
    spol = forms.ChoiceField(label='Spol', choices=_SPOL, widget=forms.Select(attrs=_WIDGET))
    datum_rodjenja = forms.DateField(label='Datum rođenja', widget=_DATE)
    mjesto_rodjenja = forms.CharField(
        label='Mjesto rođenja',
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zupa_stanovanja = forms.CharField(
        label='Župa stanovanja (ako nije ova)',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    djetetov_email = forms.EmailField(label='E-mail krizmanika', required=False)
    djetetov_telefon = forms.CharField(label='Mobitel krizmanika', max_length=30, required=False)
    skola = forms.CharField(
        label='Škola',
        max_length=160,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    razred_broj = forms.ChoiceField(
        label='Razred (broj)',
        choices=(
            ('', '— Odaberite —'),
            *tuple((str(n), str(n)) for n in range(1, 9)),
            ('zavrseno', 'Škola je završena'),
        ),
        widget=forms.Select(attrs=_WIDGET),
    )
    razred_slovo = forms.ChoiceField(
        label='Razred (odjeljenje)',
        required=False,
        choices=(('', '— Odaberite —'),) + tuple((letter, letter) for letter in 'ABCDEF'),
        widget=forms.Select(attrs=_WIDGET),
    )
    vjeronauk = forms.ChoiceField(
        label='Pohađa školski vjeronauk',
        choices=_YES_NO,
        initial='da',
        widget=forms.Select(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    vjeroucitelj = forms.CharField(
        label='Ime i prezime vjeroučitelja',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    datum_krstenja = forms.DateField(label='Datum krštenja', required=False, widget=_DATE)
    zupa_krstenja = forms.CharField(
        label='Župa krštenja',
        max_length=160,
        required=False,
        help_text='Ako krizmanik nije kršten u ovoj župi, navedite župu krštenja.',
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zupa_pricesti = forms.CharField(
        label='Župa prve pričesti',
        max_length=160,
        required=False,
        help_text='Ako prva pričest nije bila u ovoj župi, navedite tu župu.',
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    otac_ime = forms.CharField(label='Ime oca', max_length=100)
    otac_prezime = forms.CharField(label='Prezime oca', max_length=100)
    otac_telefon = forms.CharField(label='Telefon oca', max_length=30, required=False)
    otac_email = forms.EmailField(label='E-mail oca', required=False)
    majka_ime = forms.CharField(label='Ime majke', max_length=100)
    majka_prezime = forms.CharField(label='Prezime majke', max_length=100)
    majka_djevojacko = forms.CharField(label='Djevojačko prezime majke', max_length=100, required=False)
    majka_telefon = forms.CharField(label='Telefon majke', max_length=30, required=False)
    majka_email = forms.EmailField(label='E-mail majke', required=False)
    kum_ime = forms.CharField(label='Ime kuma / kume', max_length=100, required=False)
    kum_prezime = forms.CharField(label='Prezime kuma / kume', max_length=100, required=False)
    kum_spol = forms.ChoiceField(
        label='Spol kuma / kume',
        choices=_SPOL,
        required=False,
        widget=forms.Select(attrs=_WIDGET),
    )
    kum_telefon = forms.CharField(label='Telefon kuma / kume', max_length=30, required=False)
    kum_email = forms.EmailField(label='E-mail kuma / kume', required=False)
    napomena = forms.CharField(label='Napomena', required=False, widget=_TEXTAREA)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pastoralna_godina'].choices = pastoral_year_choices()
        current = pastoral_year_choices()[1][0]
        self.fields['pastoralna_godina'].initial = current
        self.fields['pastoralna_godina'].help_text = (
            f'Trenutno aktivna pastoralna godina je {current}.'
        )

    def clean(self):
        cleaned = super().clean()
        cleaned['razred'] = compose_school_class(cleaned)
        cleaned['roditelji'] = compose_baptism_parents_line(cleaned)
        cleaned['kum'] = compose_sponsor_name(cleaned)
        parent_phone = (
            str(cleaned.get('otac_telefon') or '').strip()
            or str(cleaned.get('majka_telefon') or '').strip()
        )
        parent_email = (
            str(cleaned.get('otac_email') or '').strip()
            or str(cleaned.get('majka_email') or '').strip()
        )
        if not parent_phone:
            self.add_error('otac_telefon', 'Unesite telefon barem jednog roditelja.')
            self.add_error('majka_telefon', 'Unesite telefon barem jednog roditelja.')
        if not parent_email:
            self.add_error('otac_email', 'Unesite e-mail barem jednog roditelja.')
            self.add_error('majka_email', 'Unesite e-mail barem jednog roditelja.')
        cleaned['telefon'] = (
            parent_phone
            or str(cleaned.get('djetetov_telefon') or '').strip()
            or str(cleaned.get('kum_telefon') or '').strip()
        )
        return cleaned


class KrsenjePublicForm(PublicWizardForm):
    STEPS = (
        ('termin', 'Termin'),
        ('krstenik', 'Krštenik'),
        ('otac', 'Otac'),
        ('majka', 'Majka'),
        ('kumovi', 'Kumovi'),
    )
    FIELD_STEPS = {
        'dogovoreni_datum': 'termin',
        'vrijeme': 'termin',
        'podnositelj': 'termin',
        'telefon': 'termin',
        'email': 'termin',
        'ime': 'krstenik',
        'prezime': 'krstenik',
        'spol': 'krstenik',
        'datum_rodjenja': 'krstenik',
        'mjesto_rodjenja': 'krstenik',
        'street_id': 'krstenik',
        'house_number': 'krstenik',
        'zupa_stanovanja': 'krstenik',
        'vjencani_status_roditelja': 'krstenik',
        'otac_poznat': 'otac',
        'otac_ime': 'otac',
        'otac_prezime': 'otac',
        'otac_datum_rodjenja': 'otac',
        'otac_vjeroispovijest': 'otac',
        'otac_mjesto_rodjenja': 'otac',
        'otac_telefon': 'otac',
        'majka_poznata': 'majka',
        'majka_ime': 'majka',
        'majka_prezime': 'majka',
        'majka_djevojacko': 'majka',
        'majka_datum_rodjenja': 'majka',
        'majka_vjeroispovijest': 'majka',
        'majka_mjesto_rodjenja': 'majka',
        'majka_telefon': 'majka',
        'kum1_ime': 'kumovi',
        'kum1_prezime': 'kumovi',
        'kum1_spol': 'kumovi',
        'kum1_zupa': 'kumovi',
        'kum2_ime': 'kumovi',
        'kum2_prezime': 'kumovi',
        'kum2_spol': 'kumovi',
        'kum2_zupa': 'kumovi',
        'napomena': 'kumovi',
        'gdpr_consent': 'kumovi',
    }
    ADDRESS_STEP = 'krstenik'
    WIZARD_NOTICES = (
        (
            'alert',
            'Obrazac popunite ako ste kontaktirali župni ured. Datum krštenja unesite onako kako je dogovoren; ako još nije dogovoren, unesite željeni datum i napišite napomenu.',
        ),
        (
            'note',
            'Ako je krštenik maloljetan, prijavu ispunjava roditelj ili skrbnik. Pri unosu imena pazite na dijakritike (č, ć, đ, š, ž) — pogrešan unos može ući u matičnu knjigu.',
        ),
    )
    STEP_INTROS = {
        'termin': 'Unesite dogovoreni datum, tko podnosi zahtjev i kako vas ured može javiti.',
        'krstenik': 'Podaci o kršteniku kako će se upisati u knjigu krštenih.',
        'otac': 'Ako otac nije poznat, odaberite „Ne“ i nastavite.',
        'majka': 'Djevojačko prezime pomaže pri upisu u maticu.',
        'kumovi': 'Potreban je barem jedan kum ili kuma. Župu stanovanja kuma navedite ako nije iz ove župe — ured tada traži potvrdu kuma.',
    }

    gdpr_consent = forms.BooleanField(
        label='Dajem privolu za obradu osobnih podataka u svrhu prijave i upisa u knjigu krštenih.',
        required=True,
    )
    dogovoreni_datum = forms.DateField(
        label='Datum krštenja',
        widget=_DATE,
        help_text='Datum koji ste dogovorili s župnim uredom, ili željeni datum.',
    )
    vrijeme = forms.TimeField(label='Vrijeme (ako je dogovoreno)', required=False, widget=_TIME)
    podnositelj = forms.CharField(
        label='Podnositelj zahtjeva',
        max_length=120,
        help_text='Ime i prezime roditelja ili skrbnika koji ispunjava obrazac.',
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    telefon = forms.CharField(label='Kontakt telefon', max_length=30)
    email = forms.EmailField(
        label='E-mail za povratnu obavijest',
        widget=forms.EmailInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    ime = forms.CharField(label='Ime krštenika', max_length=100)
    prezime = forms.CharField(label='Prezime krštenika', max_length=100)
    spol = forms.ChoiceField(label='Spol', choices=_SPOL, widget=forms.Select(attrs=_WIDGET))
    datum_rodjenja = forms.DateField(label='Datum rođenja', widget=_DATE)
    mjesto_rodjenja = forms.CharField(label='Mjesto rođenja', max_length=120)
    zupa_stanovanja = forms.CharField(
        label='Župa stanovanja (ako nije ova)',
        max_length=160,
        required=False,
        help_text='Ispunite samo ako obitelj ne pripada ovoj župi.',
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    vjencani_status_roditelja = forms.ChoiceField(
        label='Bračni status roditelja',
        choices=_VJENCANI_STATUS,
        required=False,
        widget=forms.Select(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    otac_poznat = forms.ChoiceField(
        label='Otac je poznat',
        choices=_YES_NO,
        initial='da',
        widget=forms.Select(attrs=_WIDGET),
    )
    otac_ime = forms.CharField(label='Ime oca', max_length=100, required=False)
    otac_prezime = forms.CharField(label='Prezime oca', max_length=100, required=False)
    otac_datum_rodjenja = forms.DateField(label='Datum rođenja oca', required=False, widget=_DATE)
    otac_vjeroispovijest = forms.ChoiceField(
        label='Vjeroispovijest oca',
        choices=_VJEROISPOVIJEST,
        required=False,
        widget=forms.Select(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    otac_mjesto_rodjenja = forms.CharField(label='Mjesto rođenja oca', max_length=120, required=False)
    otac_telefon = forms.CharField(label='Kontakt oca', max_length=30, required=False)
    majka_poznata = forms.ChoiceField(
        label='Majka je poznata',
        choices=_YES_NO,
        initial='da',
        widget=forms.Select(attrs=_WIDGET),
    )
    majka_ime = forms.CharField(label='Ime majke', max_length=100, required=False)
    majka_prezime = forms.CharField(label='Prezime majke', max_length=100, required=False)
    majka_djevojacko = forms.CharField(label='Djevojačko prezime', max_length=100, required=False)
    majka_datum_rodjenja = forms.DateField(label='Datum rođenja majke', required=False, widget=_DATE)
    majka_vjeroispovijest = forms.ChoiceField(
        label='Vjeroispovijest majke',
        choices=_VJEROISPOVIJEST,
        required=False,
        widget=forms.Select(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    majka_mjesto_rodjenja = forms.CharField(label='Mjesto rođenja majke', max_length=120, required=False)
    majka_telefon = forms.CharField(label='Kontakt majke', max_length=30, required=False)
    kum1_ime = forms.CharField(label='Ime kuma / kume', max_length=100)
    kum1_prezime = forms.CharField(label='Prezime kuma / kume', max_length=100)
    kum1_spol = forms.ChoiceField(
        label='Spol kuma / kume',
        choices=_SPOL,
        required=False,
        widget=forms.Select(attrs=_WIDGET),
    )
    kum1_zupa = forms.CharField(
        label='Župa stanovanja kuma / kume',
        max_length=160,
        required=False,
        help_text='Potrebno ako kum nije iz ove župe — ured tada traži potvrdu kuma.',
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    kum2_ime = forms.CharField(label='Ime drugog kuma / kume', max_length=100, required=False)
    kum2_prezime = forms.CharField(label='Prezime drugog kuma / kume', max_length=100, required=False)
    kum2_spol = forms.ChoiceField(
        label='Spol drugog kuma / kume',
        choices=_SPOL,
        required=False,
        widget=forms.Select(attrs=_WIDGET),
    )
    kum2_zupa = forms.CharField(
        label='Župa stanovanja drugog kuma / kume',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    napomena = forms.CharField(label='Napomena', required=False, widget=_TEXTAREA)

    def _require_known_parent(self, cleaned, known_key, fields, label):
        if str(cleaned.get(known_key) or 'da') == 'ne':
            return
        for field_name in fields:
            if not str(cleaned.get(field_name) or '').strip():
                self.add_error(field_name, f'Unesite {label}.')

    def clean(self):
        cleaned = super().clean()
        self._require_known_parent(
            cleaned, 'otac_poznat', ('otac_ime', 'otac_prezime'), 'ime i prezime oca',
        )
        self._require_known_parent(
            cleaned, 'majka_poznata', ('majka_ime', 'majka_prezime'), 'ime i prezime majke',
        )
        cleaned['ime_djeteta'] = compose_baptism_child_name(cleaned)
        cleaned['roditelji'] = compose_baptism_parents_line(cleaned)
        cleaned['kumovi'] = compose_baptism_godparents_line(cleaned)
        cleaned['kum'] = cleaned['kumovi']
        cleaned['zeljeni_termin'] = cleaned.get('dogovoreni_datum')
        return cleaned


class PricestPublicForm(PublicWizardForm):
    STEPS = (
        ('prijava', 'Prijava'),
        ('dijete', 'Prvopričesnik'),
        ('roditelji', 'Roditelji'),
    )
    FIELD_STEPS = {
        'pastoralna_godina': 'prijava',
        'podnositelj': 'prijava',
        'email': 'prijava',
        'ime': 'dijete',
        'prezime': 'dijete',
        'spol': 'dijete',
        'datum_rodjenja': 'dijete',
        'mjesto_rodjenja': 'dijete',
        'street_id': 'dijete',
        'house_number': 'dijete',
        'zupa_stanovanja': 'dijete',
        'djetetov_email': 'dijete',
        'djetetov_telefon': 'dijete',
        'skola': 'dijete',
        'razred_broj': 'dijete',
        'razred_slovo': 'dijete',
        'vjeronauk': 'dijete',
        'vjeroucitelj': 'dijete',
        'datum_krstenja': 'dijete',
        'zupa_krstenja': 'dijete',
        'otac_ime': 'roditelji',
        'otac_prezime': 'roditelji',
        'otac_telefon': 'roditelji',
        'otac_email': 'roditelji',
        'majka_ime': 'roditelji',
        'majka_prezime': 'roditelji',
        'majka_djevojacko': 'roditelji',
        'majka_telefon': 'roditelji',
        'majka_email': 'roditelji',
        'napomena': 'roditelji',
        'gdpr_consent': 'roditelji',
    }
    ADDRESS_STEP = 'dijete'
    WIZARD_NOTICES = (
        (
            'alert',
            'Prijavu ispunjava roditelj ili skrbnik. Pri unosu imena pazite na dijakritike (č, ć, đ, š, ž).',
        ),
        (
            'note',
            'Kontakt telefon i e-mail barem jednog roditelja su obavezni. Župni ured koristi ih za obavijesti o pripremi.',
        ),
    )
    STEP_INTROS = {
        'prijava': 'Odaberite pastoralnu godinu te unesite tko podnosi zahtjev i e-mail za obavijesti.',
        'dijete': 'Podaci o prvopričesniku, školi, vjeronauku i krštenju.',
        'roditelji': 'Ime i prezime oba roditelja. Djevojačko prezime majke unesite ako je poznato.',
    }

    gdpr_consent = forms.BooleanField(
        label='Dajem privolu za obradu osobnih podataka u svrhu prijave i pripreme za prvu pričest.',
        required=True,
    )
    pastoralna_godina = forms.ChoiceField(
        label='Prva pričest će biti',
        choices=pastoral_year_choices(),
        widget=forms.Select(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
        help_text='Odaberite godinu pripreme / slavlja.',
    )
    podnositelj = forms.CharField(
        label='Podnositelj zahtjeva',
        max_length=120,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    email = forms.EmailField(
        label='E-mail za obavijesti',
        widget=forms.EmailInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    ime = forms.CharField(label='Ime prvopričesnika', max_length=100)
    prezime = forms.CharField(label='Prezime prvopričesnika', max_length=100)
    spol = forms.ChoiceField(label='Spol', choices=_SPOL, widget=forms.Select(attrs=_WIDGET))
    datum_rodjenja = forms.DateField(label='Datum rođenja', widget=_DATE)
    mjesto_rodjenja = forms.CharField(
        label='Mjesto rođenja',
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zupa_stanovanja = forms.CharField(
        label='Župa stanovanja (ako nije ova)',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    djetetov_email = forms.EmailField(label='E-mail djeteta', required=False)
    djetetov_telefon = forms.CharField(label='Mobitel djeteta', max_length=30, required=False)
    skola = forms.CharField(
        label='Škola',
        max_length=160,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    razred_broj = forms.ChoiceField(
        label='Razred (broj)',
        choices=(('', '— Odaberite —'),) + tuple((str(n), str(n)) for n in range(1, 9)),
        widget=forms.Select(attrs=_WIDGET),
    )
    razred_slovo = forms.ChoiceField(
        label='Razred (odjeljenje)',
        required=False,
        choices=(('', '— Odaberite —'),) + tuple((letter, letter) for letter in 'ABCDEF'),
        widget=forms.Select(attrs=_WIDGET),
    )
    vjeronauk = forms.ChoiceField(
        label='Pohađa školski vjeronauk',
        choices=_YES_NO,
        initial='da',
        widget=forms.Select(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    vjeroucitelj = forms.CharField(
        label='Ime i prezime vjeroučitelja',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    datum_krstenja = forms.DateField(label='Datum krštenja', required=False, widget=_DATE)
    zupa_krstenja = forms.CharField(
        label='Župa krštenja',
        max_length=160,
        required=False,
        help_text='Ako dijete nije kršteno u ovoj župi, navedite župu krštenja.',
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    otac_ime = forms.CharField(label='Ime oca', max_length=100)
    otac_prezime = forms.CharField(label='Prezime oca', max_length=100)
    otac_telefon = forms.CharField(label='Telefon oca', max_length=30, required=False)
    otac_email = forms.EmailField(label='E-mail oca', required=False)
    majka_ime = forms.CharField(label='Ime majke', max_length=100)
    majka_prezime = forms.CharField(label='Prezime majke', max_length=100)
    majka_djevojacko = forms.CharField(label='Djevojačko prezime majke', max_length=100, required=False)
    majka_telefon = forms.CharField(label='Telefon majke', max_length=30, required=False)
    majka_email = forms.EmailField(label='E-mail majke', required=False)
    napomena = forms.CharField(label='Napomena', required=False, widget=_TEXTAREA)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pastoralna_godina'].choices = pastoral_year_choices()
        current = pastoral_year_choices()[1][0]
        self.fields['pastoralna_godina'].initial = current
        self.fields['pastoralna_godina'].help_text = (
            f'Trenutno aktivna pastoralna godina je {current}.'
        )

    def clean(self):
        cleaned = super().clean()
        cleaned['ime_djeteta'] = compose_baptism_child_name(cleaned)
        cleaned['razred'] = compose_school_class(cleaned)
        cleaned['roditelji'] = compose_baptism_parents_line(cleaned)
        parent_phone = (
            str(cleaned.get('otac_telefon') or '').strip()
            or str(cleaned.get('majka_telefon') or '').strip()
        )
        parent_email = (
            str(cleaned.get('otac_email') or '').strip()
            or str(cleaned.get('majka_email') or '').strip()
        )
        if not parent_phone:
            self.add_error('otac_telefon', 'Unesite telefon barem jednog roditelja.')
            self.add_error('majka_telefon', 'Unesite telefon barem jednog roditelja.')
        if not parent_email:
            self.add_error('otac_email', 'Unesite e-mail barem jednog roditelja.')
            self.add_error('majka_email', 'Unesite e-mail barem jednog roditelja.')
        cleaned['telefon'] = (
            parent_phone
            or str(cleaned.get('djetetov_telefon') or '').strip()
        )
        return cleaned


class UkopPublicForm(PublicFormBase):
    pokojnik = forms.CharField(label='Ime i prezime pokojnika', max_length=120)
    datum_smrti = forms.DateField(label='Datum smrti', widget=_DATE)
    kontakt = forms.CharField(
        label='Kontakt osoba (ime)',
        max_length=120,
        widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'Ime i prezime kontakt osobe'}),
    )
    telefon = forms.CharField(label='Kontakt telefon', max_length=30)
    email = forms.EmailField(label='E-mail', required=False)
    groblje = forms.CharField(
        label='Groblje / mjesto ukopa',
        max_length=200,
        widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'Naziv groblja i mjesto'}),
    )
    dogovoreno_vrijeme = forms.CharField(
        label='Dogovoreno vrijeme ukopa',
        max_length=50,
        widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'npr. 14:00'}),
    )
    zeljeni_datum = forms.DateField(label='Željeni datum pogreba', required=False, widget=_DATE)
    napomena = forms.CharField(
        label='Napomena (liturgija, posebne želje)',
        required=False,
        widget=_TEXTAREA,
    )


class VjencanjePublicForm(PublicWizardForm):
    STEPS = (
        ('zupa', 'Župa'),
        ('zarucnik', 'Zaručnik'),
        ('zarucnica', 'Zaručnica'),
        ('kumovi', 'Kumovi'),
    )
    FIELD_STEPS = {
        'dogovoreni_datum': 'zupa',
        'vrijeme': 'zupa',
        'podnositelj': 'zupa',
        'email': 'zupa',
        'zupa_vjencanja_ista': 'zupa',
        'zupa_vjencanja': 'zupa',
        'zarucnik_ime': 'zarucnik',
        'zarucnik_prezime': 'zarucnik',
        'zarucnik_datum_rodjenja': 'zarucnik',
        'zarucnik_mjesto_rodjenja': 'zarucnik',
        'zarucnik_vjeroispovijest': 'zarucnik',
        'zarucnik_mjesto': 'zarucnik',
        'zarucnik_ulica': 'zarucnik',
        'zarucnik_kbr': 'zarucnik',
        'zarucnik_zupa_stanovanja': 'zarucnik',
        'zarucnik_telefon': 'zarucnik',
        'zarucnik_email': 'zarucnik',
        'zarucnik_otac_ime': 'zarucnik',
        'zarucnik_otac_prezime': 'zarucnik',
        'zarucnik_majka_ime': 'zarucnik',
        'zarucnik_majka_djevojacko': 'zarucnik',
        'zarucnik_datum_krstenja': 'zarucnik',
        'zarucnik_zupa_krstenja': 'zarucnik',
        'zarucnik_datum_krizme': 'zarucnik',
        'zarucnik_zupa_krizme': 'zarucnik',
        'zarucnik_druge_zupe': 'zarucnik',
        'zarucnica_ime': 'zarucnica',
        'zarucnica_rodjeno_prezime': 'zarucnica',
        'zarucnica_civilno_prezime': 'zarucnica',
        'zarucnica_datum_rodjenja': 'zarucnica',
        'zarucnica_mjesto_rodjenja': 'zarucnica',
        'zarucnica_vjeroispovijest': 'zarucnica',
        'zarucnica_mjesto': 'zarucnica',
        'zarucnica_ulica': 'zarucnica',
        'zarucnica_kbr': 'zarucnica',
        'zarucnica_zupa_stanovanja': 'zarucnica',
        'zarucnica_telefon': 'zarucnica',
        'zarucnica_email': 'zarucnica',
        'zarucnica_otac_ime': 'zarucnica',
        'zarucnica_otac_prezime': 'zarucnica',
        'zarucnica_majka_ime': 'zarucnica',
        'zarucnica_majka_djevojacko': 'zarucnica',
        'zarucnica_datum_krstenja': 'zarucnica',
        'zarucnica_zupa_krstenja': 'zarucnica',
        'zarucnica_datum_krizme': 'zarucnica',
        'zarucnica_zupa_krizme': 'zarucnica',
        'zarucnica_druge_zupe': 'zarucnica',
        'svjedok1_ime': 'kumovi',
        'svjedok1_prezime': 'kumovi',
        'svjedok1_spol': 'kumovi',
        'svjedok1_mjesto': 'kumovi',
        'svjedok1_ulica': 'kumovi',
        'svjedok1_kbr': 'kumovi',
        'svjedok2_ime': 'kumovi',
        'svjedok2_prezime': 'kumovi',
        'svjedok2_spol': 'kumovi',
        'svjedok2_mjesto': 'kumovi',
        'svjedok2_ulica': 'kumovi',
        'svjedok2_kbr': 'kumovi',
        'napomena': 'kumovi',
        'gdpr_consent': 'kumovi',
    }
    ADDRESS_STEP = ''
    WIZARD_NOTICES = (
        (
            'alert',
            'Ženidbeni postupak vodi ova župa. Prijava nije rezervacija termina; ured će vas kontaktirati.',
        ),
        (
            'note',
            'Podatke o sakramentima prepišite s krsnog i slobodnog lista. Ako osoba nije krštena ili datum nije poznat, ostavite ta polja prazna.',
        ),
    )
    STEP_INTROS = {
        'zupa': 'Unesite dogovoreni datum i tko podnosi zahtjev. Ako će se ženidba sklopiti u drugoj župi, navedite je.',
        'zarucnik': 'Osobni podaci, trenutna adresa, roditelji te krštenje i krizma zaručnika.',
        'zarucnica': 'Osobni podaci, trenutna adresa, roditelji te krštenje i krizma zaručnice.',
        'kumovi': 'Dva svjedoka (kuma). Adresa svjedoka nije obavezna.',
    }

    gdpr_consent = forms.BooleanField(
        label='Dajem privolu za obradu osobnih podataka u svrhu prijave i vođenja ženidbenog postupka.',
        required=True,
    )
    dogovoreni_datum = forms.DateField(
        label='Dogovoreni datum vjenčanja',
        widget=_DATE,
    )
    vrijeme = forms.TimeField(
        label='Vrijeme (ako je dogovoreno)',
        required=False,
        widget=_TIME,
    )
    podnositelj = forms.CharField(
        label='Podnositelj zahtjeva',
        max_length=120,
        widget=forms.TextInput(attrs={
            **_WIDGET,
            'class': 'form-control form-control--wide',
            'placeholder': 'Vaše ime i prezime',
        }),
    )
    email = forms.EmailField(
        label='E-mail za obavijesti',
        widget=forms.EmailInput(attrs={
            **_WIDGET,
            'class': 'form-control form-control--wide',
            'placeholder': 'Vaš e-mail',
        }),
    )
    zupa_vjencanja_ista = forms.ChoiceField(
        label='Sakrament vjenčanja sklopit ćete',
        choices=(
            ('da', 'U ovoj župi'),
            ('ne', 'U drugoj župi'),
        ),
        initial='da',
        widget=forms.Select(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zupa_vjencanja = forms.CharField(
        label='Župa u kojoj će se sklopiti ženidba',
        max_length=200,
        required=False,
        help_text=(
            'Ispunite samo ako nije ova župa. Ako je župa izvan RH, unesite puni naziv.'
        ),
        widget=forms.TextInput(attrs={
            **_WIDGET,
            'class': 'form-control form-control--wide',
            'placeholder': 'Župa vjenčanja',
        }),
    )

    zarucnik_ime = forms.CharField(label='Ime zaručnika', max_length=100)
    zarucnik_prezime = forms.CharField(label='Prezime zaručnika', max_length=100)
    zarucnik_datum_rodjenja = forms.DateField(
        label='Datum rođenja zaručnika', widget=_DATE,
    )
    zarucnik_mjesto_rodjenja = forms.CharField(
        label='Mjesto rođenja zaručnika',
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zarucnik_vjeroispovijest = forms.ChoiceField(
        label='Vjeroispovijest / obrednost zaručnika',
        choices=_VJEROISPOVIJEST,
        widget=forms.Select(attrs=_WIDGET),
    )
    zarucnik_mjesto = forms.CharField(
        label='Grad / mjesto stanovanja zaručnika',
        max_length=120,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    zarucnik_ulica = forms.CharField(
        label='Ulica stanovanja zaručnika',
        max_length=160,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zarucnik_kbr = forms.CharField(label='Kućni broj', max_length=30)
    zarucnik_zupa_stanovanja = forms.CharField(
        label='Župa stanovanja zaručnika (ako nije ova)',
        max_length=160,
        required=False,
        help_text='Unesite trenutnu župu stanovanja bez obzira na građanski prijavljeno prebivalište.',
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zarucnik_telefon = forms.CharField(
        label='Telefon / mobitel zaručnika', max_length=30, required=False,
    )
    zarucnik_email = forms.EmailField(
        label='E-mail zaručnika (neobavezno)', required=False,
    )
    zarucnik_otac_ime = forms.CharField(
        label='Ime oca zaručnika', max_length=100, required=False,
    )
    zarucnik_otac_prezime = forms.CharField(
        label='Prezime oca zaručnika', max_length=100, required=False,
    )
    zarucnik_majka_ime = forms.CharField(
        label='Ime majke zaručnika', max_length=100, required=False,
    )
    zarucnik_majka_djevojacko = forms.CharField(
        label='Djevojačko prezime majke zaručnika', max_length=100, required=False,
    )
    zarucnik_datum_krstenja = forms.DateField(
        label='Datum krštenja zaručnika',
        required=False,
        widget=_DATE,
        help_text='Ako zaručnik nije kršten ili datum nije poznat, ostavite prazno.',
    )
    zarucnik_zupa_krstenja = forms.CharField(
        label='Župa krštenja zaručnika',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zarucnik_datum_krizme = forms.DateField(
        label='Datum krizme zaručnika',
        required=False,
        widget=_DATE,
        help_text='Ako krizma nije primljena ili datum nije poznat, ostavite prazno.',
    )
    zarucnik_zupa_krizme = forms.CharField(
        label='Župa krizme zaručnika',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zarucnik_druge_zupe = forms.CharField(
        label='Druge župe stanovanja zaručnika nakon 16. godine',
        required=False,
        help_text=(
            'Župe u kojima je živio dulje od tri mjeseca. Ne navodite trenutnu župu stanovanja.'
        ),
        widget=_TEXTAREA,
    )

    zarucnica_ime = forms.CharField(label='Ime zaručnice', max_length=100)
    zarucnica_rodjeno_prezime = forms.CharField(
        label='Rođeno prezime zaručnice', max_length=100,
    )
    zarucnica_civilno_prezime = forms.CharField(
        label='Civilno udano prezime zaručnice',
        max_length=100,
        required=False,
        help_text='Ispunite samo ako je zaručnica već sklopila građanski brak.',
        widget=forms.TextInput(attrs=_WIDGET),
    )
    zarucnica_datum_rodjenja = forms.DateField(
        label='Datum rođenja zaručnice', widget=_DATE,
    )
    zarucnica_mjesto_rodjenja = forms.CharField(
        label='Mjesto rođenja zaručnice',
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zarucnica_vjeroispovijest = forms.ChoiceField(
        label='Vjeroispovijest / obrednost zaručnice',
        choices=_VJEROISPOVIJEST,
        widget=forms.Select(attrs=_WIDGET),
    )
    zarucnica_mjesto = forms.CharField(
        label='Grad / mjesto stanovanja zaručnice',
        max_length=120,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    zarucnica_ulica = forms.CharField(
        label='Ulica stanovanja zaručnice',
        max_length=160,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zarucnica_kbr = forms.CharField(label='Kućni broj', max_length=30)
    zarucnica_zupa_stanovanja = forms.CharField(
        label='Župa stanovanja zaručnice (ako nije ova)',
        max_length=160,
        required=False,
        help_text='Unesite trenutnu župu stanovanja bez obzira na građanski prijavljeno prebivalište.',
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zarucnica_telefon = forms.CharField(
        label='Telefon / mobitel zaručnice', max_length=30, required=False,
    )
    zarucnica_email = forms.EmailField(
        label='E-mail zaručnice (neobavezno)', required=False,
    )
    zarucnica_otac_ime = forms.CharField(
        label='Ime oca zaručnice', max_length=100, required=False,
    )
    zarucnica_otac_prezime = forms.CharField(
        label='Prezime oca zaručnice', max_length=100, required=False,
    )
    zarucnica_majka_ime = forms.CharField(
        label='Ime majke zaručnice', max_length=100, required=False,
    )
    zarucnica_majka_djevojacko = forms.CharField(
        label='Djevojačko prezime majke zaručnice', max_length=100, required=False,
    )
    zarucnica_datum_krstenja = forms.DateField(
        label='Datum krštenja zaručnice',
        required=False,
        widget=_DATE,
        help_text='Ako zaručnica nije krštena ili datum nije poznat, ostavite prazno.',
    )
    zarucnica_zupa_krstenja = forms.CharField(
        label='Župa krštenja zaručnice',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zarucnica_datum_krizme = forms.DateField(
        label='Datum krizme zaručnice',
        required=False,
        widget=_DATE,
        help_text='Ako krizma nije primljena ili datum nije poznat, ostavite prazno.',
    )
    zarucnica_zupa_krizme = forms.CharField(
        label='Župa krizme zaručnice',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'class': 'form-control form-control--wide'}),
    )
    zarucnica_druge_zupe = forms.CharField(
        label='Druge župe stanovanja zaručnice nakon 14. godine',
        required=False,
        help_text=(
            'Župe u kojima je živjela dulje od tri mjeseca. Ne navodite trenutnu župu stanovanja.'
        ),
        widget=_TEXTAREA,
    )

    svjedok1_ime = forms.CharField(label='Ime svjedoka zaručnika', max_length=100)
    svjedok1_prezime = forms.CharField(
        label='Prezime svjedoka zaručnika', max_length=100,
    )
    svjedok1_spol = forms.ChoiceField(
        label='Spol svjedoka zaručnika',
        choices=_SPOL,
        widget=forms.Select(attrs=_WIDGET),
    )
    svjedok1_mjesto = forms.CharField(
        label='Grad svjedoka zaručnika', max_length=120, required=False,
    )
    svjedok1_ulica = forms.CharField(
        label='Ulica svjedoka zaručnika', max_length=160, required=False,
    )
    svjedok1_kbr = forms.CharField(
        label='Kućni broj svjedoka zaručnika', max_length=30, required=False,
    )
    svjedok2_ime = forms.CharField(label='Ime svjedoka zaručnice', max_length=100)
    svjedok2_prezime = forms.CharField(
        label='Prezime svjedoka zaručnice', max_length=100,
    )
    svjedok2_spol = forms.ChoiceField(
        label='Spol svjedoka zaručnice',
        choices=_SPOL,
        widget=forms.Select(attrs=_WIDGET),
    )
    svjedok2_mjesto = forms.CharField(
        label='Grad svjedoka zaručnice', max_length=120, required=False,
    )
    svjedok2_ulica = forms.CharField(
        label='Ulica svjedoka zaručnice', max_length=160, required=False,
    )
    svjedok2_kbr = forms.CharField(
        label='Kućni broj svjedoka zaručnice', max_length=30, required=False,
    )
    napomena = forms.CharField(
        label='Napomena',
        required=False,
        widget=_TEXTAREA,
    )

    def _init_street_field(self):
        return

    def resolved_address(self) -> str:
        cleaned = getattr(self, 'cleaned_data', {}) or {}

        def line(prefix):
            return ' '.join(
                str(part or '').strip()
                for part in (
                    cleaned.get(f'{prefix}_ulica'),
                    cleaned.get(f'{prefix}_kbr'),
                    cleaned.get(f'{prefix}_mjesto'),
                )
                if str(part or '').strip()
            )

        return ' · '.join(part for part in (line('zarucnik'), line('zarucnica')) if part)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('zupa_vjencanja_ista') == 'ne' and not str(
            cleaned.get('zupa_vjencanja') or ''
        ).strip():
            self.add_error(
                'zupa_vjencanja',
                'Unesite župu u kojoj će se sklopiti ženidba.',
            )
        if cleaned.get('zupa_vjencanja_ista') == 'da':
            cleaned['zupa_vjencanja'] = ''
        groom_phone = str(cleaned.get('zarucnik_telefon') or '').strip()
        bride_phone = str(cleaned.get('zarucnica_telefon') or '').strip()
        if not groom_phone and not bride_phone:
            self.add_error('zarucnik_telefon', 'Unesite telefon barem jednog od mladenca.')
            self.add_error('zarucnica_telefon', 'Unesite telefon barem jednog od mladenca.')
        cleaned['telefon'] = groom_phone or bride_phone
        cleaned['par'] = compose_couple_name(cleaned)
        cleaned['kumovi'] = compose_wedding_witnesses_line(cleaned)
        return cleaned


PUBLIC_FORM_CLASSES = {
    'prijava-krizma': KrizmaPublicForm,
    'prijava-krsenje': KrsenjePublicForm,
    'prijava-pricest': PricestPublicForm,
    'prijava-ukop': UkopPublicForm,
    'prijava-vjencanje': VjencanjePublicForm,
}

PUBLIC_FORM_INTROS = {
    'prijava-krizma': 'Prijava krizmanika. Obrazac ispunjava roditelj ili skrbnik ako je kandidat maloljetan.',
    'prijava-krsenje': 'Prijava za sakrament krštenja. Obrazac ispunjava roditelj ili skrbnik.',
    'prijava-pricest': 'Prijava prvopričesnika. Obrazac ispunjava roditelj ili skrbnik.',
    'prijava-ukop': 'Obrazac za dogovor pogreba i ukopa. U hitnim slučajevima nazovite župni ured.',
    'prijava-vjencanje': 'Prijava za sakrament ženidbe. Ženidbeni postupak vodi ova župa; slavlje može biti i u drugoj.',
}
