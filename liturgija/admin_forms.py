from django.core.exceptions import ValidationError
from django import  forms

from liturgija.models import LiturgicalCalendarEntry
from liturgija.services.liturgical_imports import manual_celebration_identity


class CalendarYearImportForm(forms.Form):
    year = forms.IntegerField(
        label='Godina',
        min_value=2000,
        max_value=2100,
    )


class LiturgicalCalendarEntryForm(forms.ModelForm):
    class Meta:
        model = LiturgicalCalendarEntry
        fields = (
            'date', 'name', 'original_name', 'liturgical_color',
            'priority', 'priority_label',
        )
        widgets = {
            'liturgical_color': forms.Select,
        }

    def clean(self):
        cleaned_data = super().clean()
        entry_date = cleaned_data.get('date')
        name = cleaned_data.get('name')
        if entry_date and name:
            identity = manual_celebration_identity(entry_date, name)
            duplicate = LiturgicalCalendarEntry.objects.filter(
                provider=LiturgicalCalendarEntry.Provider.MANUAL,
                date=entry_date,
                external_identifier=identity,
            )
            if self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise ValidationError(
                    'Ručni unos istog slavlja na taj datum već postoji.'
                )
        return cleaned_data