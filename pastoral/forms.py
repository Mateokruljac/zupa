from django import forms

_WIDGET = {'class': 'form-control'}


class LoginForm(forms.Form):
    email = forms.EmailField(
        label='E-mail',
        initial='ured@zupa-bdm-sb.hr',
        widget=forms.EmailInput(attrs={**_WIDGET, 'autocomplete': 'email'}),
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
    title = forms.CharField(label='Zadatak', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    owner = forms.CharField(label='Odgovorna osoba', max_length=100, widget=forms.TextInput(attrs=_WIDGET))
    due = forms.DateField(label='Rok', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    priority = forms.ChoiceField(label='Prioritet', choices=[('visoka', 'Visoka'), ('srednja', 'Srednja'), ('niska', 'Niska')], widget=forms.Select(attrs=_WIDGET))
    category = forms.CharField(label='Područje', max_length=50, required=False, widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'npr. biskupija, ŽPV, ured'}))


class EventForm(forms.Form):
    title = forms.CharField(label='Događaj / termin', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    event_date = forms.DateField(label='Datum', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    event_time = forms.TimeField(label='Vrijeme', required=False, widget=forms.TimeInput(attrs={'type': 'time', **_WIDGET}))
    place = forms.CharField(label='Prostor / lokacija', max_length=120, required=False, widget=forms.TextInput(attrs=_WIDGET))
    event_type = forms.ChoiceField(
        label='Vrsta',
        choices=[
            ('pastoral', 'Pastoral'), ('liturgija', 'Liturgija'), ('ured', 'Župni ured'),
            ('vijece', 'Vijeće'), ('biskupija', 'Biskupija'), ('privatno', 'Privatni termin'),
        ],
        widget=forms.Select(attrs=_WIDGET),
    )
    owner = forms.CharField(label='Odgovorna osoba', max_length=100, widget=forms.TextInput(attrs=_WIDGET))
    notes = forms.CharField(label='Priprema / napomena', required=False, widget=forms.Textarea(attrs={'rows': 2, **_WIDGET}))


COUNCIL_TYPE_CHOICES = (
    ('pastoral', 'Župno pastoralno vijeće (ŽPV)'),
    ('economic', 'Župno ekonomsko vijeće (ŽEV)'),
)


class CouncilMemberForm(forms.Form):
    council_type = forms.ChoiceField(
        label='Vijeće',
        choices=COUNCIL_TYPE_CHOICES,
        widget=forms.Select(attrs=_WIDGET),
    )
    name = forms.CharField(
        label='Ime i prezime člana',
        max_length=120,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    role = forms.CharField(
        label='Uloga',
        max_length=120,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    confirmed = forms.BooleanField(
        label='Članstvo je potvrđeno',
        required=False,
        initial=True,
    )


class CouncilMeetingForm(forms.Form):
    council_type = forms.ChoiceField(
        label='Vijeće',
        choices=COUNCIL_TYPE_CHOICES,
        widget=forms.Select(attrs=_WIDGET),
    )
    meeting_date = forms.DateField(
        label='Datum sljedećeg sastanka ili pregleda',
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )


class ConfirmationGroupForm(forms.Form):
    year = forms.IntegerField(widget=forms.HiddenInput())
    ceremony_date = forms.DateField(
        label='Datum krizme',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    bishop = forms.CharField(
        label='Biskup / celebrant',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    group_fee = forms.DecimalField(
        label='Grupna naknada (€)',
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs=_WIDGET),
    )
    group_fee_paid = forms.BooleanField(
        label='Grupna naknada je plaćena',
        required=False,
    )


class ConfirmationCandidateForm(forms.Form):
    year = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(
        label='Ime i prezime krizmanika',
        max_length=160,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    birth_date = forms.DateField(
        label='Datum rođenja',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    school = forms.CharField(label='Škola', max_length=160, required=False, widget=forms.TextInput(attrs=_WIDGET))
    school_class = forms.CharField(label='Razred', max_length=30, required=False, widget=forms.TextInput(attrs=_WIDGET))
    formation_group = forms.CharField(label='Skupina', max_length=60, required=False, widget=forms.TextInput(attrs=_WIDGET))
    baptism_date = forms.DateField(
        label='Datum krštenja',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    sponsor = forms.CharField(label='Kum/ka', max_length=160, required=False, widget=forms.TextInput(attrs=_WIDGET))
    status = forms.ChoiceField(
        label='Status',
        choices=(
            ('priprema', 'Priprema'),
            ('pristupnica', 'Pristupnica'),
            ('potvrđen', 'Potvrđen'),
        ),
        widget=forms.Select(attrs=_WIDGET),
    )


class FirstCommunionCandidateForm(forms.Form):
    year = forms.IntegerField(widget=forms.HiddenInput())
    first_name = forms.CharField(label='Ime', max_length=100, widget=forms.TextInput(attrs=_WIDGET))
    last_name = forms.CharField(label='Prezime', max_length=100, widget=forms.TextInput(attrs=_WIDGET))
    school = forms.CharField(label='Škola', max_length=160, required=False, widget=forms.TextInput(attrs=_WIDGET))
    school_class = forms.CharField(label='Razred', max_length=30, required=False, widget=forms.TextInput(attrs=_WIDGET))
    parents = forms.CharField(label='Roditelji / skrbnici', max_length=200, required=False, widget=forms.TextInput(attrs=_WIDGET))
    status = forms.CharField(label='Status', max_length=60, required=False, initial='priprema', widget=forms.TextInput(attrs=_WIDGET))
    paid = forms.BooleanField(label='Naknada je plaćena', required=False)


class FamilyForm(forms.Form):
    surname = forms.CharField(label='Prezime obitelji', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    street_id = forms.ChoiceField(label='Ulica', choices=(), required=False, widget=forms.Select(attrs=_WIDGET))
    address = forms.CharField(label='Adresa i kućni broj', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    phone = forms.CharField(label='Telefon', max_length=50, required=False, widget=forms.TextInput(attrs=_WIDGET))
    email = forms.EmailField(label='E-mail', required=False, widget=forms.EmailInput(attrs=_WIDGET))
    origin_place = forms.CharField(label='Mjesto podrijetla', max_length=120, required=False, widget=forms.TextInput(attrs=_WIDGET))

    def __init__(self, *args, streets=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['street_id'].choices = [('', '— Bez povezane ulice —')] + [
            (street.get('id'), street.get('name', ''))
            for street in (streets or [])
            if street.get('id')
        ]


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


class InterparishRequestForm(forms.Form):
    target_parish = forms.ChoiceField(label='Župa primatelj', choices=(), widget=forms.Select(attrs=_WIDGET))
    request_type = forms.ChoiceField(
        label='Vrsta zahtjeva',
        choices=[
            ('marriage_certificate', 'Potvrda za ženidbeni postupak'),
            ('baptism_certificate', 'Krsni list / potvrda krštenja'),
            ('marriage_delegation', 'Delegacija za ženidbu'),
            ('priest_substitution', 'Zamjena svećenika'),
            ('mass_intention_transfer', 'Prijenos misnih nakana'),
            ('sacrament_record_check', 'Provjera sakramentalnog zapisa'),
            ('pastoral_handover', 'Pastoralna primopredaja'),
        ],
        widget=forms.Select(attrs=_WIDGET),
    )
    subject = forms.CharField(label='Predmet', max_length=180, widget=forms.TextInput(attrs=_WIDGET))
    person_name = forms.CharField(
        label='Osoba / osobe na koje se zahtjev odnosi',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'autocomplete': 'off'}),
    )
    case_reference = forms.CharField(
        label='Veza s predmetom u župi',
        max_length=60,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'npr. ŽEN-2026-018'}),
    )
    due_date = forms.DateField(label='Rok odgovora', widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    priority = forms.ChoiceField(
        label='Prioritet',
        choices=[('normal', 'Redovno'), ('high', 'Visoko'), ('urgent', 'Hitno')],
        widget=forms.Select(attrs=_WIDGET),
    )
    confidentiality = forms.ChoiceField(
        label='Razina povjerljivosti',
        choices=[('interno', 'Interno'), ('povjerljivo', 'Povjerljivo')],
        widget=forms.Select(attrs=_WIDGET),
    )
    description = forms.CharField(
        label='Opis i napomena primatelju',
        widget=forms.Textarea(attrs={'rows': 4, **_WIDGET}),
    )

    def __init__(self, *args, parishes=None, active_parish_id='', **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_parish'].choices = [
            (parish.get('id'), f"{parish.get('name')} · {parish.get('city', '')}")
            for parish in (parishes or [])
            if parish.get('id') and parish.get('id') != active_parish_id
        ]


class OfficeEntryForm(forms.Form):
    direction = forms.ChoiceField(
        label='Smjer',
        choices=[('incoming', 'Ulazno'), ('outgoing', 'Izlazno')],
        widget=forms.Select(attrs=_WIDGET),
    )
    channel = forms.ChoiceField(
        label='Kanal',
        choices=[
            ('in_person', 'Osobno u uredu'), ('phone', 'Telefon'), ('email', 'E-mail'),
            ('post', 'Pošta'), ('diocese', 'Biskupija'), ('web', 'Javni obrazac'),
        ],
        widget=forms.Select(attrs=_WIDGET),
    )
    subject = forms.CharField(label='Predmet', max_length=180, widget=forms.TextInput(attrs=_WIDGET))
    contact = forms.CharField(label='Osoba / ustanova', max_length=140, required=False, widget=forms.TextInput(attrs=_WIDGET))
    linked_case = forms.CharField(
        label='Veza s postojećim predmetom', max_length=60, required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'npr. KRŠ-2026-024'}),
    )
    due_date = forms.DateField(label='Rok', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    owner = forms.CharField(label='Odgovorna osoba', max_length=100, required=False, widget=forms.TextInput(attrs=_WIDGET))
    priority = forms.ChoiceField(
        label='Prioritet',
        choices=[('normal', 'Redovno'), ('high', 'Visoko'), ('urgent', 'Hitno')],
        widget=forms.Select(attrs=_WIDGET),
    )
    confidentiality = forms.ChoiceField(
        label='Povjerljivost',
        choices=[('službeno', 'Službeno'), ('interno', 'Interno'), ('povjerljivo', 'Povjerljivo'), ('strogo povjerljivo', 'Strogo povjerljivo')],
        widget=forms.Select(attrs=_WIDGET),
    )
    note = forms.CharField(label='Bilješka i sljedeći korak', required=False, widget=forms.Textarea(attrs={'rows': 4, **_WIDGET}))


class FacilityIssueForm(forms.Form):
    facility = forms.CharField(label='Objekt / prostor', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    title = forms.CharField(label='Problem ili zahvat', max_length=180, widget=forms.TextInput(attrs=_WIDGET))
    risk = forms.ChoiceField(
        label='Razina rizika',
        choices=[('low', 'Nisko'), ('medium', 'Srednje'), ('high', 'Visoko')],
        widget=forms.Select(attrs=_WIDGET),
    )
    due_date = forms.DateField(label='Rok', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    owner = forms.CharField(label='Odgovorna osoba', max_length=100, required=False, widget=forms.TextInput(attrs=_WIDGET))
    supplier = forms.CharField(label='Izvođač / dobavljač', max_length=120, required=False, widget=forms.TextInput(attrs=_WIDGET))
    estimated_cost = forms.DecimalField(
        label='Procijenjeni trošak (€)', max_digits=12, decimal_places=2, required=False,
        widget=forms.NumberInput(attrs={**_WIDGET, 'min': '0', 'step': '0.01'}),
    )
    description = forms.CharField(label='Opis i sljedeći korak', required=False, widget=forms.Textarea(attrs={'rows': 4, **_WIDGET}))


class CommunicationPlanForm(forms.Form):
    title = forms.CharField(label='Naziv komunikacije', max_length=180, widget=forms.TextInput(attrs=_WIDGET))
    audience = forms.CharField(
        label='Ciljana skupina', max_length=180,
        widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'npr. roditelji krizmanika s privolom za e-mail'}),
    )
    channel = forms.ChoiceField(
        label='Kanal',
        choices=[
            ('email', 'E-mail'), ('sms', 'SMS'), ('email_sms', 'E-mail i SMS'),
            ('app', 'Obavijest u aplikaciji'), ('web', 'Web objava'), ('print', 'Poštanska / tiskana pošiljka'),
        ],
        widget=forms.Select(attrs=_WIDGET),
    )
    scheduled_at = forms.DateTimeField(
        label='Planirano slanje', required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', **_WIDGET}),
    )
    requires_approval = forms.BooleanField(label='Prije slanja traži odobrenje župnika', required=False)
    message = forms.CharField(label='Poruka / sadržaj', widget=forms.Textarea(attrs={'rows': 5, **_WIDGET}))


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
