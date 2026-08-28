from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
        required=True,
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
