"""Obrasci za sakramente i sakramentalnu pripravu."""
from django import forms

_WIDGET = {'class': 'form-control'}


class ConfirmationYearForm(forms.Form):
    year = forms.IntegerField(
        label='Nova godina',
        min_value=1900,
        max_value=2100,
        widget=forms.NumberInput(attrs=_WIDGET),
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


class ConfirmationYearCreateForm(ConfirmationGroupForm):
    year = forms.IntegerField(
        label='Godina',
        min_value=1900,
        max_value=2100,
        widget=forms.NumberInput(attrs=_WIDGET),
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


class FirstCommunionYearForm(forms.Form):
    year = forms.IntegerField(
        label='Nova godina',
        min_value=1900,
        max_value=2100,
        widget=forms.NumberInput(attrs=_WIDGET),
    )


class FirstCommunionGroupForm(forms.Form):
    year = forms.IntegerField(widget=forms.HiddenInput())
    group_name = forms.CharField(
        label='Naziv skupine',
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    ceremony_date = forms.DateField(
        label='Datum prve pričesti',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    celebrant = forms.CharField(
        label='Svećenik',
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


class FirstCommunionYearCreateForm(FirstCommunionGroupForm):
    year = forms.IntegerField(
        label='Godina',
        min_value=1900,
        max_value=2100,
        widget=forms.NumberInput(attrs=_WIDGET),
    )


class BaptismForm(forms.Form):
    child_name = forms.CharField(label='Ime djeteta', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    birth_date = forms.DateField(label='Datum rođenja', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    baptism_date = forms.DateField(label='Datum krštenja', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    parents = forms.CharField(label='Roditelji', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    godparents = forms.CharField(label='Kumovi', max_length=200, required=False, widget=forms.TextInput(attrs=_WIDGET))
    godparent_certificate_received = forms.BooleanField(label='Potvrda kuma je zaprimljena', required=False)
    celebrant = forms.CharField(label='Svećenik', max_length=100, required=False, widget=forms.TextInput(attrs=_WIDGET))
    registry_number = forms.CharField(label='Matični broj', max_length=60, required=False, widget=forms.TextInput(attrs=_WIDGET))
    status = forms.CharField(label='Status', max_length=50, required=False, initial='planirano', widget=forms.TextInput(attrs=_WIDGET))
    stipend = forms.DecimalField(label='Stipendij', max_digits=8, decimal_places=2, initial=0, required=False, widget=forms.NumberInput(attrs=_WIDGET))


class WeddingForm(forms.Form):
    couple = forms.CharField(label='Par', max_length=200, widget=forms.TextInput(attrs=_WIDGET))
    wedding_date = forms.DateField(label='Datum vjenčanja', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    church = forms.CharField(label='Crkva', max_length=160, required=False, widget=forms.TextInput(attrs=_WIDGET))
    contact = forms.CharField(label='Kontakt para', max_length=100, required=False, widget=forms.TextInput(attrs=_WIDGET))
    celebrant = forms.CharField(label='Svećenik', max_length=100, required=False, widget=forms.TextInput(attrs=_WIDGET))
    preparatory_sessions = forms.IntegerField(label='Broj susreta priprave', min_value=0, required=False, initial=0, widget=forms.NumberInput(attrs=_WIDGET))
    documents_ok = forms.BooleanField(label='Dokumenti su potpuni', required=False)
    witnesses = forms.CharField(label='Svjedoci', max_length=240, required=False, widget=forms.TextInput(attrs=_WIDGET))
    status = forms.CharField(label='Status', max_length=50, required=False, initial='planirano', widget=forms.TextInput(attrs=_WIDGET))
    stipend = forms.DecimalField(label='Stipendij', max_digits=8, decimal_places=2, initial=0, required=False, widget=forms.NumberInput(attrs=_WIDGET))


class FuneralForm(forms.Form):
    deceased = forms.CharField(label='Pokojnik', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    funeral_date = forms.DateField(label='Datum pogreba', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    cemetery = forms.CharField(label='Groblje', max_length=120, required=False, widget=forms.TextInput(attrs=_WIDGET))
    family_contact = forms.CharField(label='Kontakt obitelji', max_length=160, required=False, widget=forms.TextInput(attrs=_WIDGET))
    celebrant = forms.CharField(label='Svećenik', max_length=100, required=False, widget=forms.TextInput(attrs=_WIDGET))
    mass_planned = forms.BooleanField(label='Planirana misa zadušnica', required=False)
    mass_date = forms.DateField(label='Datum mise zadušnice', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    mass_time = forms.TimeField(label='Vrijeme mise', required=False, widget=forms.TimeInput(attrs={'type': 'time', **_WIDGET}))
    status = forms.CharField(label='Status', max_length=50, required=False, initial='planirano', widget=forms.TextInput(attrs=_WIDGET))
    stipend = forms.DecimalField(label='Stipendij', max_digits=8, decimal_places=2, initial=0, required=False, widget=forms.NumberInput(attrs=_WIDGET))


class AnointingForm(forms.Form):
    person = forms.CharField(label='Osoba', max_length=120, widget=forms.TextInput(attrs=_WIDGET))
    scheduled = forms.DateField(label='Datum', required=False, widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}))
    priest = forms.CharField(label='Svećenik', max_length=100, required=False, widget=forms.TextInput(attrs=_WIDGET))
    address = forms.CharField(label='Adresa', max_length=200, required=False, widget=forms.TextInput(attrs=_WIDGET))
    contact = forms.CharField(label='Kontakt', max_length=50, required=False, widget=forms.TextInput(attrs=_WIDGET))
    status = forms.CharField(label='Status', max_length=50, required=False, initial='planirano', widget=forms.TextInput(attrs=_WIDGET))
