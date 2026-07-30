from django.conf import settings
from django.db import models


class Parish(models.Model):
    """Jedna župa — podaci i postavke (struktura kao bivši localStorage)."""

    slug = models.SlugField(unique=True, default=settings.PARISH_DEFAULT_SLUG)
    settings = models.JSONField(default=dict, blank=True)
    data = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Župa'
        verbose_name_plural = 'Župe'

    def __str__(self):
        return self.settings.get('name', self.slug)


class OtpChallenge(models.Model):
    """OTP kod za prijavu (demo / produkcija)."""

    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6)
    role = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
