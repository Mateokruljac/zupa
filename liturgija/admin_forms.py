"""Obrasci Django admina za uvoz godine i ručni red kalendara."""
from django import forms
from django.core.exceptions import ValidationError

from django_multitenant.schema import with_tenant_schema
from liturgija.models import LiturgicalCalendarEntry

PRIMARY_HELP = (
    'Ako označite ovo slavlje kao glavno, drugo glavno slavlje '
    'na isti dan bit će odznačeno.'
)


class CalendarYearImportForm(forms.Form):
    """Samo godina (2000–2100) za gumb „Uvezi Romcal”."""

    year = forms.IntegerField(label='Godina')


class LiturgicalCalendarEntryForm(forms.ModelForm):
    """Ručni unos slavlja; blokira duplikat istog naziva na datumu."""

    class Meta:
        model = LiturgicalCalendarEntry
        fields = (
            'date',
            'name',
            'original_name',
            'liturgical_color',
            'priority',
            'priority_label',
            'is_primary',
            'readings',
        )
        widgets = {
            'liturgical_color': forms.Select,
            'priority_label': forms.Select,
        }

    @with_tenant_schema
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['priority_label'].choices = [
            ('', '---------'),
            *LiturgicalCalendarEntry.PriorityLabel.choices,
        ]
        # Stari uvozni natpis koji nije u dropdownu — zadrži ga kao opciju.
        current = (self.instance.priority_label or '').strip()
        if current and current not in dict(LiturgicalCalendarEntry.PriorityLabel.choices):
            self.fields['priority_label'].choices = [
                ('', '---------'),
                (current, current),
                *LiturgicalCalendarEntry.PriorityLabel.choices,
            ]
        other_primary = self._other_primary(self._resolve_date())
        if other_primary:
            self.fields['is_primary'].help_text = (
                f'Na ovaj dan je već glavno: „{other_primary.name}”. '
                'Ako označite ovo slavlje kao primarno, to će biti odznačeno.'
            )
            if not self.instance.pk and not self.is_bound:
                self.fields['is_primary'].initial = False
        else:
            self.fields['is_primary'].help_text = PRIMARY_HELP
            if not self.instance.pk and not self.is_bound:
                self.fields['is_primary'].initial = True

    def _resolve_date(self):
        if self.is_bound:
            raw = self.data.get(self.add_prefix('date'))
            return raw or None
        if self.instance.pk:
            return self.instance.date
        return self.initial.get('date')

    @with_tenant_schema
    def _other_primary(self, entry_date):
        if not entry_date:
            return None
        queryset = LiturgicalCalendarEntry.objects.filter(
            date=entry_date,
            is_primary=True,
        )
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        return queryset.first()

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
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise ValidationError(
                    'Ručni unos istog slavlja na taj datum već postoji.'
                )
        return cleaned_data
