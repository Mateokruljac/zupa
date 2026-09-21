"""Obrasci Django admina za uvoz godine i ručni red kalendara."""
from django.core.exceptions import ValidationError
from django import  forms

from liturgija.models import LiturgicalCalendarEntry
from django_multitenant.schema import with_tenant_schema


class CalendarYearImportForm(forms.Form):
    """Samo godina (2000–2100) za gumb „Uvezi Romcal”."""

    year = forms.IntegerField(
        label='Godina',
        min_value=2000,
        max_value=2100,
    )


class LiturgicalCalendarEntryForm(forms.ModelForm):
    """Ručni unos slavlja; blokira duplikat istog naziva na datumu."""

    class Meta:
        model = LiturgicalCalendarEntry
        fields = (
            'date', 'name', 'original_name', 'liturgical_color',
            'priority', 'priority_label',
        )
        widgets = {
            'liturgical_color': forms.Select,
        }

    @with_tenant_schema
    def clean(self):
        cleaned_data = super().clean()
        entry_date = cleaned_data.get('date')
        name = cleaned_data.get('name')
        if entry_date and name:
            duplicate = LiturgicalCalendarEntry.objects.filter(
                provider=LiturgicalCalendarEntry.Provider.MANUAL,
                date=entry_date,
                name=name,
            )
            if self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)  # vlastiti red nije duplikat
            if duplicate.exists():
                raise ValidationError(
                    'Ručni unos istog slavlja na taj datum već postoji.'
                )
        return cleaned_data
