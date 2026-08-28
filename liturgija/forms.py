"""Obrasci za misne nakane."""
from django import forms

_WIDGET = {'class': 'form-control'}


class IntentionForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', **_WIDGET}),
    )
    mass_time = forms.CharField(
        label='Vrijeme mise',
        max_length=10,
        widget=forms.TextInput(attrs={**_WIDGET, 'placeholder': 'npr. 09:00'}),
    )
    requested_by = forms.CharField(
        label='Naručitelj',
        max_length=100,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    intention_for = forms.CharField(
        label='Nakana za',
        max_length=200,
        widget=forms.TextInput(attrs=_WIDGET),
    )
    stipend = forms.DecimalField(
        label='Stipendij',
        max_digits=8,
        decimal_places=2,
        initial=30,
        widget=forms.NumberInput(attrs=_WIDGET),
    )
    paid = forms.BooleanField(label='Plaćeno', required=False)
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, **_WIDGET}),
    )
