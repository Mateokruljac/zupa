"""Obrasci za župni ured: kalendar, vijeća i postavke."""
from django import forms

_WIDGET = {'class': 'form-control'}


class ParishSettingsForm(forms.Form):
    name = forms.CharField(
        label='Puni naziv župe',
        max_length=200,
        widget=forms.TextInput(attrs={**_WIDGET, 'autocomplete': 'organization'}),
    )
    short_name = forms.CharField(
        label='Naziv u zaglavlju',
        max_length=100,
        required=False,
        help_text='Kraći naziv koji se prikazuje u vrhu aplikacije.',
        widget=forms.TextInput(attrs=_WIDGET),
    )
    city = forms.CharField(
        label='Mjesto',
        max_length=100,
        widget=forms.TextInput(attrs={**_WIDGET, 'autocomplete': 'address-level2'}),
    )
    diocese = forms.CharField(
        label='Nadbiskupija ili biskupija',
        max_length=200,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    pastor = forms.CharField(
        label='Župnik',
        max_length=100,
        widget=forms.TextInput(attrs={**_WIDGET, 'autocomplete': 'name'}),
    )
    phone = forms.CharField(
        label='Telefon župnog ureda',
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'autocomplete': 'tel'}),
    )
    email = forms.EmailField(
        label='E-mail župe',
        required=False,
        widget=forms.EmailInput(attrs={**_WIDGET, 'autocomplete': 'email'}),
    )
    primary_color = forms.CharField(
        label='Glavna boja',
        max_length=7,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'type': 'color'}),
    )
    accent_color = forms.CharField(
        label='Naglasna boja',
        max_length=7,
        required=False,
        widget=forms.TextInput(attrs={**_WIDGET, 'type': 'color'}),
    )
    logo_url = forms.URLField(
        label='Poveznica na logotip',
        required=False,
        widget=forms.URLInput(attrs={**_WIDGET, 'placeholder': 'https://…'}),
    )
    default_mass_intention_stipend = forms.DecimalField(
        label='Uobičajeni stipendij za misnu nakanu (€)',
        max_digits=8,
        decimal_places=2,
        min_value=0,
        required=False,
        help_text='Služi samo kao početna vrijednost i može se promijeniti pri unosu.',
        widget=forms.NumberInput(attrs={**_WIDGET, 'min': '0', 'step': '0.01'}),
    )


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
    phone = forms.CharField(
        label='Kontakt broj mobitela',
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={
            **_WIDGET,
            'type': 'tel',
            'inputmode': 'tel',
            'autocomplete': 'tel',
            'placeholder': 'npr. 091 123 4567',
        }),
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
