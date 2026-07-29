from django import forms

from users.models import User


_WIDGET = {'class': 'form-control'}


class LoginForm(forms.Form):
    email = forms.EmailField(
        label='E-mail',
        initial='ured@zupa-bdm-sb.hr',
        widget=forms.EmailInput(attrs={**_WIDGET, 'autocomplete': 'email'}),
    )
    role = forms.ChoiceField(
        label='Uloga',
        choices=User.ROLE_CHOICES,
        initial='zupnik',
        widget=forms.Select(attrs=_WIDGET),
    )
    gdpr_consent = forms.BooleanField(
        label='Slažem se s obradom podataka u svrhu pristupa župnom uredu (GDPR).',
        required=True,
    )


class OtpVerifyForm(forms.Form):
    code = forms.CharField(
        label='Kod za prijavu',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'login-otp-input',
            'id': 'login-otp-input',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'maxlength': '6',
            'placeholder': '000000',
        }),
    )


class ParishSettingsForm(forms.Form):
    name = forms.CharField(label='Naziv župe', max_length=200)
    short_name = forms.CharField(label='Kratki naziv', max_length=100, required=False)
    city = forms.CharField(label='Mjesto', max_length=100)
    diocese = forms.CharField(label='Biskupija', max_length=200)
    pastor = forms.CharField(label='Župnik', max_length=100)
    phone = forms.CharField(label='Telefon', max_length=30, required=False)
    email = forms.EmailField(label='E-mail župe', required=False)
    primary_color = forms.CharField(label='Glavna boja', max_length=7, required=False)
    accent_color = forms.CharField(label='Zlatna boja', max_length=7, required=False)
    logo_url = forms.URLField(label='Logo URL', required=False)


class TaskForm(forms.Form):
    title = forms.CharField(max_length=200)
    due = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    priority = forms.ChoiceField(choices=[('visoka', 'Visoka'), ('srednja', 'Srednja'), ('niska', 'Niska')])
    category = forms.CharField(max_length=50, required=False)


class IntentionForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    mass_time = forms.CharField(label='Vrijeme mise', max_length=10, widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'npr. 09:00'}))
    requested_by = forms.CharField(label='Naručitelj', max_length=100, widget=forms.TextInput(attrs=_WIDGET))
    intention_for = forms.CharField(label='Nakana za', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    stipend = forms.DecimalField(label='Stipendij', max_digits=8, decimal_places=2, initial=30, widget=forms.NumberInput(attrs=_WIDGET))
    paid = forms.BooleanField(label='Plaćeno', required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2, **_WIDGET}))


class ParishDebtForm(forms.Form):
    label = forms.CharField(label='Opis', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    amount = forms.DecimalField(label='Iznos (€)', max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs=_WIDGET))
    category = forms.ChoiceField(
        label='Kategorija',
        choices=[
            ('režije', 'Režije'),
            ('dobavljaci', 'Dobavljači'),
            ('dz', 'Biskupija / DŽ'),
            ('ostalo', 'Ostalo'),
        ],
        widget=forms.Select(attrs=_WIDGET),
    )
    due_date = forms.DateField(label='Rok', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    contact = forms.CharField(label='Kontakt', max_length=100, required=False, widget=forms.TextInput(attrs=_WIDGET))
    notes = forms.CharField(label='Napomena', required=False, widget=forms.Textarea(attrs={'rows': 2, **_WIDGET}))


class BaptismForm(forms.Form):
    child_name = forms.CharField(label='Ime djeteta', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    baptism_date = forms.DateField(label='Datum krštenja', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    parents = forms.CharField(label='Roditelji', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    status = forms.CharField(label='Status', max_length=50, required=False, initial='planirano', widget=forms.TextInput(attrs=_WIDGET))
    stipend = forms.DecimalField(label='Stipendij', max_digits=8, decimal_places=2, initial=0, required=False, widget=forms.NumberInput(attrs=_WIDGET))


class WeddingForm(forms.Form):
    couple = forms.CharField(label='Par', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    wedding_date = forms.DateField(label='Datum vjenčanja', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    status = forms.CharField(label='Status', max_length=50, required=False, initial='planirano', widget=forms.TextInput(attrs=_WIDGET))
    stipend = forms.DecimalField(label='Stipendij', max_digits=8, decimal_places=2, initial=0, required=False, widget=forms.NumberInput(attrs=_WIDGET))


class FuneralForm(forms.Form):
    deceased = forms.CharField(label='Pokojnik', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    funeral_date = forms.DateField(label='Datum pogreba', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    cemetery = forms.CharField(label='Groblje', max_length=120, required=False, widget=forms.TextInput(attrs=_WIDGET))
    status = forms.CharField(label='Status', max_length=50, required=False, initial='planirano', widget=forms.TextInput(attrs=_WIDGET))
    stipend = forms.DecimalField(label='Stipendij', max_digits=8, decimal_places=2, initial=0, required=False, widget=forms.NumberInput(attrs=_WIDGET))


class AnointingForm(forms.Form):
    person = forms.CharField(label='Osoba', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    scheduled = forms.DateField(label='Datum', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    priest = forms.CharField(label='Svećenik', max_length=100, required=False, widget=forms.TextInput(attrs=_WIDGET))
    address = forms.CharField(label='Adresa', max_length=200, required=False, widget=forms.TextInput(attrs=_WIDGET))
    contact = forms.CharField(label='Kontakt', max_length=50, required=False, widget=forms.TextInput(attrs=_WIDGET))
    status = forms.CharField(label='Status', max_length=50, required=False, initial='planirano', widget=forms.TextInput(attrs=_WIDGET))
    stipend = forms.DecimalField(label='Stipendij', max_digits=8, decimal_places=2, initial=0, required=False, widget=forms.NumberInput(attrs=_WIDGET))


class StreetForm(forms.Form):
    name = forms.CharField(label='Naziv ulice', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    zone = forms.CharField(label='Zona / kvart', max_length=80, required=False, widget=forms.TextInput(attrs=_WIDGET))
    notes = forms.CharField(label='Napomena', required=False, widget=forms.Textarea(attrs={'rows': 2, **_WIDGET}))


class CashbookEntryForm(forms.Form):
    date = forms.DateField(label='Datum', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    entry_type = forms.ChoiceField(
        label='Tip',
        choices=[('ulaz', 'Ulaz'), ('izlaz', 'Izlaz')],
        widget=forms.Select(attrs=_WIDGET),
    )
    ledger = forms.ChoiceField(
        label='Dnevnik',
        choices=[('plavi', 'Plavi'), ('crveni', 'Crveni')],
        initial='plavi',
        widget=forms.Select(attrs=_WIDGET),
    )
    category = forms.CharField(label='Kategorija', max_length=60, widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'npr. lukno, režije'}))
    description = forms.CharField(label='Opis', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    amount = forms.DecimalField(label='Iznos (€)', max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs=_WIDGET))
    payment_method = forms.CharField(
        label='Način plaćanja',
        max_length=40,
        required=False,
        initial='gotovina',
        widget=forms.TextInput(attrs=_WIDGET),
    )


class InvoiceForm(forms.Form):
    number = forms.CharField(label='Broj računa', max_length=60, widget=forms.TextInput(attrs=_WIDGET))
    issue_date = forms.DateField(label='Datum računa', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    due_date = forms.DateField(label='Rok plaćanja', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    supplier_name = forms.CharField(label='Dobavljač', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    category = forms.ChoiceField(
        label='Kategorija',
        choices=[
            ('režije', 'Režije'),
            ('dobavljaci', 'Dobavljači'),
            ('dz', 'Biskupija / DŽ'),
            ('ostalo', 'Ostalo'),
        ],
        widget=forms.Select(attrs=_WIDGET),
    )
    description = forms.CharField(label='Opis', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    amount = forms.DecimalField(label='Iznos (€)', max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs=_WIDGET))


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
    family_id = forms.CharField(label='Obitelj (ID)', max_length=40, required=False, widget=forms.TextInput(attrs=_WIDGET))
    report = forms.CharField(label='Izvještaj', required=False, widget=forms.Textarea(attrs={'rows': 3, **_WIDGET}))


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


STREET_NOT_LISTED = '__other__'

_DATE = forms.DateInput(attrs={'type': 'date', **_WIDGET})
_TEXTAREA = forms.Textarea(attrs={'rows': 3, **_WIDGET})


class PublicFormBase(forms.Form):
    gdpr_consent = forms.BooleanField(
        label='Slažem se s obradom osobnih podataka u svrhu pastoralne prijave (GDPR).',
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
        from collections import OrderedDict

        tail = ('street_id', 'house_number', 'gdpr_consent')
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


class KrizmaPublicForm(PublicFormBase):
    ime = forms.CharField(label='Ime krizmanika', max_length=100)
    prezime = forms.CharField(label='Prezime krizmanika', max_length=100)
    datum_rodjenja = forms.DateField(label='Datum rođenja', widget=_DATE)
    skola = forms.CharField(label='Škola', max_length=120)
    razred = forms.CharField(label='Razred', max_length=20)
    roditelji = forms.CharField(
        label='Roditelji / skrbnici',
        max_length=200,
        widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'Ime i prezime roditelja'}),
    )
    kum = forms.CharField(
        label='Kum/ka za krizmu',
        max_length=120,
        widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'Ime i prezime kuma/ke'}),
    )
    datum_krstenja = forms.DateField(label='Datum krštenja', required=False, widget=_DATE)
    telefon = forms.CharField(label='Kontakt telefon', max_length=30)
    email = forms.EmailField(label='E-mail', required=False)
    napomena = forms.CharField(label='Napomena', required=False, widget=_TEXTAREA)


class KrsenjePublicForm(PublicFormBase):
    ime_djeteta = forms.CharField(label='Ime i prezime djeteta', max_length=120)
    datum_rodjenja = forms.DateField(label='Datum rođenja djeteta', widget=_DATE)
    mjesto_rodjenja = forms.CharField(label='Mjesto rođenja', max_length=100, required=False)
    roditelji = forms.CharField(
        label='Roditelji',
        max_length=200,
        widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'Ime i prezime roditelja'}),
    )
    kum = forms.CharField(
        label='Kum/ka',
        max_length=120,
        widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'Ime i prezime kuma/ke'}),
    )
    telefon = forms.CharField(label='Kontakt telefon', max_length=30)
    email = forms.EmailField(label='E-mail', required=False)
    zeljeni_termin = forms.DateField(label='Željeni termin krštenja', required=False, widget=_DATE)
    napomena = forms.CharField(label='Napomena', required=False, widget=_TEXTAREA)


class PricestPublicForm(PublicFormBase):
    ime_djeteta = forms.CharField(label='Ime i prezime djeteta', max_length=120)
    datum_rodjenja = forms.DateField(label='Datum rođenja', widget=_DATE)
    skola = forms.CharField(label='Škola', max_length=120)
    razred = forms.CharField(label='Razred', max_length=20)
    roditelji = forms.CharField(
        label='Roditelji',
        max_length=200,
        widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'Ime i prezime roditelja'}),
    )
    datum_krstenja = forms.DateField(label='Datum krštenja', required=False, widget=_DATE)
    telefon = forms.CharField(label='Kontakt telefon', max_length=30)
    email = forms.EmailField(label='E-mail', required=False)
    napomena = forms.CharField(label='Napomena', required=False, widget=_TEXTAREA)


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


PUBLIC_FORM_CLASSES = {
    'prijava-krizma': KrizmaPublicForm,
    'prijava-krsenje': KrsenjePublicForm,
    'prijava-pricest': PricestPublicForm,
    'prijava-ukop': UkopPublicForm,
}

PUBLIC_FORM_INTROS = {
    'prijava-krizma': 'Ispunite obrazac za upis krizmanika. Župni ured će vas kontaktirati.',
    'prijava-krsenje': 'Prijava djeteta za sakrament krštenja. Molimo popunite što je moguće točnije.',
    'prijava-pricest': 'Prijava prvopričesnika. Program pripreme dogovara se s župnim uredom.',
    'prijava-ukop': 'Obrazac za dogovor pogreba i ukopa. U hitnim slučajevima nazovite župni ured.',
}
