"""Kontrola kvalitete između Romcal Croatia i postojećeg LitCal izvora."""
from __future__ import annotations


def audit_liturgical_days(romcal_days: dict[str, dict], litcal_days: dict[str, dict]) -> dict:
    """Vrati razlike kao podatke za provjeru, ne kao automatske pogreške."""
    dates = sorted(set(romcal_days) | set(litcal_days))
    multiple_observances = []
    source_differences = []
    untranslated = []
    missing = []

    for iso in dates:
        romcal = romcal_days.get(iso)
        litcal = litcal_days.get(iso)
        if not romcal or not litcal or litcal.get('source') == 'offline':
            missing.append({
                'date': iso,
                'romcal': bool(romcal),
                'litcal': bool(litcal and litcal.get('source') != 'offline'),
            })
            continue

        observances = romcal.get('observances') or []
        if len(observances) > 1:
            multiple_observances.append({
                'date': iso,
                'observances': [
                    {
                        'title': item.get('title'),
                        'rankLabel': item.get('rankLabel'),
                        'colorLabel': item.get('colorLabel'),
                        'primary': bool(item.get('primary')),
                    }
                    for item in observances
                ],
            })

        differences = {}
        for field in ('title', 'color', 'rankLabel'):
            if romcal.get(field) != litcal.get(field):
                differences[field] = {
                    'romcal': romcal.get(field),
                    'litcal': litcal.get(field),
                }
        if differences:
            source_differences.append({'date': iso, 'differences': differences})

        untranslated_items = [
            item.get('titleOriginal') or item.get('title')
            for item in observances
            if not item.get('translated', romcal.get('translated', False))
        ]
        if untranslated_items:
            untranslated.append({'date': iso, 'titles': untranslated_items})

    return {
        'daysChecked': len(dates),
        'summary': {
            'multipleObservances': len(multiple_observances),
            'sourceDifferences': len(source_differences),
            'untranslated': len(untranslated),
            'missingProviderData': len(missing),
        },
        'multipleObservances': multiple_observances,
        'sourceDifferences': source_differences,
        'untranslated': untranslated,
        'missingProviderData': missing,
    }
