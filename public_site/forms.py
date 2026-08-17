from django import forms

from .models import ParishWebsite, ParishWebsiteMedia


MAX_WEBSITE_IMAGE_BYTES = 8 * 1024 * 1024
MAX_WEBSITE_IMAGE_PIXELS = 36_000_000
ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP'}


class ParishWebsiteForm(forms.ModelForm):
    class Meta:
        model = ParishWebsite
        fields = (
            'site_name', 'tagline', 'about_text', 'template_key',
            'primary_color', 'accent_color', 'contact_email', 'phone',
            'address', 'office_hours', 'confession_schedule', 'iban',
            'donation_recipient', 'donation_purpose', 'map_url',
            'facebook_url', 'youtube_url', 'instagram_url', 'custom_domain',
        )
        labels = {
            'site_name': 'Naziv stranice',
            'tagline': 'Kratka poruka',
            'about_text': 'O župi',
            'template_key': 'Predložak',
            'primary_color': 'Glavna boja',
            'accent_color': 'Naglašena boja',
            'custom_domain': 'Vlastita domena',
            'contact_email': 'Javni e-mail',
            'phone': 'Javni telefon',
            'address': 'Adresa crkve i ureda',
            'office_hours': 'Radno vrijeme župnog ureda',
            'confession_schedule': 'Vrijeme za ispovijed',
            'iban': 'IBAN za donacije',
            'donation_recipient': 'Primatelj donacije',
            'donation_purpose': 'Opis plaćanja',
            'map_url': 'Poveznica na kartu',
            'facebook_url': 'Facebook',
            'youtube_url': 'YouTube',
            'instagram_url': 'Instagram',
        }
        help_texts = {
            'template_key': (
                'Klasični je svečan i uravnotežen; Topli pastoralni je mekši i prisniji; '
                'Suvremeni je čist, geometrijski i naglašen.'
            ),
        }
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color'}),
            'tagline': forms.TextInput(attrs={
                'placeholder': 'Dobro došli u našu župnu zajednicu',
            }),
            'about_text': forms.Textarea(attrs={'rows': 4}),
            'office_hours': forms.Textarea(attrs={'rows': 3}),
            'confession_schedule': forms.Textarea(attrs={'rows': 3}),
            'iban': forms.TextInput(attrs={'placeholder': 'HR00 0000 0000 0000 0000 0'}),
            'custom_domain': forms.TextInput(attrs={
                'placeholder': 'www.ime-zupe.hr',
            }),
        }

    def clean_iban(self):
        iban = ''.join((self.cleaned_data.get('iban') or '').split()).upper()
        if iban and (not iban.startswith('HR') or len(iban) != 21 or not iban[2:].isdigit()):
            raise forms.ValidationError('Upišite hrvatski IBAN u obliku HR + 19 znamenki.')
        return iban


class ParishWebsiteMediaForm(forms.ModelForm):
    class Meta:
        model = ParishWebsiteMedia
        fields = ('image', 'alt_text', 'caption')
        labels = {
            'image': 'Fotografija',
            'alt_text': 'Opis fotografije za pristupačnost',
            'caption': 'Natpis ispod fotografije',
        }
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'accept': 'image/jpeg,image/png,image/webp',
            }),
            'alt_text': forms.TextInput(attrs={
                'placeholder': 'Npr. Procesija ispred župne crkve',
            }),
            'caption': forms.TextInput(attrs={
                'placeholder': 'Natpis koji će vidjeti posjetitelji',
            }),
        }

    def clean_image(self):
        uploaded = self.cleaned_data['image']
        if uploaded.size > MAX_WEBSITE_IMAGE_BYTES:
            raise forms.ValidationError('Fotografija smije imati najviše 8 MB.')
        image = getattr(uploaded, 'image', None)
        image_format = str(getattr(image, 'format', '')).upper()
        if image_format not in ALLOWED_IMAGE_FORMATS:
            raise forms.ValidationError('Dopušteni su JPG, PNG i WebP formati.')
        width, height = image.size
        if width * height > MAX_WEBSITE_IMAGE_PIXELS:
            raise forms.ValidationError('Fotografija ima preveliku rezoluciju.')
        if width < 600 or height < 400:
            raise forms.ValidationError('Fotografija mora imati barem 600 × 400 piksela.')
        uploaded.seek(0)
        return uploaded
