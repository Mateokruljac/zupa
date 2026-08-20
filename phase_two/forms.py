"""Obrasci koji se učitavaju samo kada je aktivirana faza 2."""
from django import forms


FORM_WIDGET_ATTRIBUTES = {'class': 'form-control'}


class InterparishRequestForm(forms.Form):
    target_parish = forms.ChoiceField(
        label='Župa primatelj',
        choices=(),
        widget=forms.Select(attrs=FORM_WIDGET_ATTRIBUTES),
    )
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
        widget=forms.Select(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    subject = forms.CharField(
        label='Predmet',
        max_length=180,
        widget=forms.TextInput(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    person_name = forms.CharField(
        label='Osoba / osobe na koje se zahtjev odnosi',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={
            **FORM_WIDGET_ATTRIBUTES,
            'autocomplete': 'off',
        }),
    )
    case_reference = forms.CharField(
        label='Veza s predmetom u župi',
        max_length=60,
        required=False,
        widget=forms.TextInput(attrs={
            **FORM_WIDGET_ATTRIBUTES,
            'placeholder': 'npr. ŽEN-2026-018',
        }),
    )
    due_date = forms.DateField(
        label='Rok odgovora',
        widget=forms.DateInput(attrs={
            'type': 'date',
            **FORM_WIDGET_ATTRIBUTES,
        }),
    )
    priority = forms.ChoiceField(
        label='Prioritet',
        choices=[
            ('normal', 'Redovno'),
            ('high', 'Visoko'),
            ('urgent', 'Hitno'),
        ],
        widget=forms.Select(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    confidentiality = forms.ChoiceField(
        label='Razina povjerljivosti',
        choices=[
            ('interno', 'Interno'),
            ('povjerljivo', 'Povjerljivo'),
        ],
        widget=forms.Select(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    description = forms.CharField(
        label='Opis i napomena primatelju',
        widget=forms.Textarea(attrs={
            'rows': 4,
            **FORM_WIDGET_ATTRIBUTES,
        }),
    )

    def __init__(
        self,
        *args,
        parishes=None,
        active_parish_id='',
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.fields['target_parish'].choices = [
            (
                parish.get('id'),
                f"{parish.get('name')} · {parish.get('city', '')}",
            )
            for parish in (parishes or [])
            if parish.get('id') and parish.get('id') != active_parish_id
        ]


class OfficeEntryForm(forms.Form):
    direction = forms.ChoiceField(
        label='Smjer',
        choices=[('incoming', 'Ulazno'), ('outgoing', 'Izlazno')],
        widget=forms.Select(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    channel = forms.ChoiceField(
        label='Kanal',
        choices=[
            ('in_person', 'Osobno u uredu'),
            ('phone', 'Telefon'),
            ('email', 'E-mail'),
            ('post', 'Pošta'),
            ('diocese', 'Biskupija'),
            ('web', 'Javni obrazac'),
        ],
        widget=forms.Select(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    subject = forms.CharField(
        label='Predmet',
        max_length=180,
        widget=forms.TextInput(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    contact = forms.CharField(
        label='Osoba / ustanova',
        max_length=140,
        required=False,
        widget=forms.TextInput(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    linked_case = forms.CharField(
        label='Veza s postojećim predmetom',
        max_length=60,
        required=False,
        widget=forms.TextInput(attrs={
            **FORM_WIDGET_ATTRIBUTES,
            'placeholder': 'npr. KRŠ-2026-024',
        }),
    )
    due_date = forms.DateField(
        label='Rok',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            **FORM_WIDGET_ATTRIBUTES,
        }),
    )
    owner = forms.CharField(
        label='Odgovorna osoba',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    priority = forms.ChoiceField(
        label='Prioritet',
        choices=[
            ('normal', 'Redovno'),
            ('high', 'Visoko'),
            ('urgent', 'Hitno'),
        ],
        widget=forms.Select(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    confidentiality = forms.ChoiceField(
        label='Povjerljivost',
        choices=[
            ('službeno', 'Službeno'),
            ('interno', 'Interno'),
            ('povjerljivo', 'Povjerljivo'),
            ('strogo povjerljivo', 'Strogo povjerljivo'),
        ],
        widget=forms.Select(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    note = forms.CharField(
        label='Bilješka i sljedeći korak',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            **FORM_WIDGET_ATTRIBUTES,
        }),
    )


class FacilityIssueForm(forms.Form):
    facility = forms.CharField(
        label='Objekt / prostor',
        max_length=120,
        widget=forms.TextInput(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    title = forms.CharField(
        label='Problem ili zahvat',
        max_length=180,
        widget=forms.TextInput(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    risk = forms.ChoiceField(
        label='Razina rizika',
        choices=[
            ('low', 'Nisko'),
            ('medium', 'Srednje'),
            ('high', 'Visoko'),
        ],
        widget=forms.Select(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    due_date = forms.DateField(
        label='Rok',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            **FORM_WIDGET_ATTRIBUTES,
        }),
    )
    owner = forms.CharField(
        label='Odgovorna osoba',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    supplier = forms.CharField(
        label='Izvođač / dobavljač',
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    estimated_cost = forms.DecimalField(
        label='Procijenjeni trošak (€)',
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            **FORM_WIDGET_ATTRIBUTES,
            'min': '0',
            'step': '0.01',
        }),
    )
    description = forms.CharField(
        label='Opis i sljedeći korak',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            **FORM_WIDGET_ATTRIBUTES,
        }),
    )


class CommunicationPlanForm(forms.Form):
    title = forms.CharField(
        label='Naziv komunikacije',
        max_length=180,
        widget=forms.TextInput(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    audience = forms.CharField(
        label='Ciljana skupina',
        max_length=180,
        widget=forms.TextInput(attrs={
            **FORM_WIDGET_ATTRIBUTES,
            'placeholder': 'npr. roditelji krizmanika s privolom za e-mail',
        }),
    )
    channel = forms.ChoiceField(
        label='Kanal',
        choices=[
            ('email', 'E-mail'),
            ('sms', 'SMS'),
            ('email_sms', 'E-mail i SMS'),
            ('app', 'Obavijest u aplikaciji'),
            ('web', 'Web objava'),
            ('print', 'Poštanska / tiskana pošiljka'),
        ],
        widget=forms.Select(attrs=FORM_WIDGET_ATTRIBUTES),
    )
    scheduled_at = forms.DateTimeField(
        label='Planirano slanje',
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            **FORM_WIDGET_ATTRIBUTES,
        }),
    )
    requires_approval = forms.BooleanField(
        label='Prije slanja traži odobrenje župnika',
        required=False,
    )
    message = forms.CharField(
        label='Poruka / sadržaj',
        widget=forms.Textarea(attrs={
            'rows': 5,
            **FORM_WIDGET_ATTRIBUTES,
        }),
    )
