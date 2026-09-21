"""Kanonska tradicija — latinska Crkva ili istočna (Križevačka eparhija).

Nije Crkva sui iuris kao zasebna tablica: u Hrvatskoj su to dva slučaja.
Nije ni obred (`LiturgicalTradition`): obred kaže kako se slavi,
ova vrijednost kaže kojoj kanonskoj obitelji župa, jurisdikcija ili osoba pripada.
"""
from django.db import models


class CanonicalTradition(models.TextChoices):
    """Latinska ili istočna kanonska tradicija."""

    LATIN = 'latin', 'Latinska'
    EASTERN = 'eastern', 'Istočna'
