"""Offline prijevod latinskih liturgijskih naziva (LitCal) na hrvatski."""
from __future__ import annotations

import re

# Rimski brojevi → arapski (za nedjelje i tjedne)
_ROMAN = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
    'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13,
    'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19,
    'XX': 20, 'XXI': 21, 'XXII': 22, 'XXIII': 23, 'XXIV': 24, 'XXV': 25,
    'XXVI': 26, 'XXVII': 27, 'XXVIII': 28, 'XXIX': 29, 'XXX': 30,
    'XXXI': 31, 'XXXII': 32, 'XXXIII': 33, 'XXXIV': 34,
}

_UNIT_ORD = {
    'prima': 1, 'primæ': 1,
    'secunda': 2, 'secundæ': 2,
    'tertia': 3, 'tertiæ': 3,
    'quarta': 4, 'quartæ': 4,
    'quinta': 5, 'quintæ': 5,
    'sexta': 6, 'sextæ': 6,
    'septima': 7, 'septimæ': 7,
    'octava': 8, 'octavæ': 8,
    'nona': 9, 'nonæ': 9,
}

_TENS_ORD = {
    'decima': 10, 'decimæ': 10,
    'undecima': 11, 'undecimæ': 11,
    'duodecima': 12, 'duodecimæ': 12,
    'duodevicesima': 18, 'duodevicesimæ': 18,
    'undevicesima': 19, 'undevicesimæ': 19,
    'vigesima': 20, 'vigesimæ': 20,
    'trigesima': 30, 'trigesimæ': 30,
}

_WEEKDAY_FERIA = {
    'II': 'Ponedjeljak',
    'III': 'Utorak',
    'IV': 'Srijeda',
    'V': 'Četvrtak',
    'VI': 'Petak',
}

# Točni nazivi blagdana (prije općih zamjena)
_EXACT: dict[str, str] = {
    'Dominica Paschæ in Resurrectione Domini': 'Uskrsna nedjelja',
    'Dominica Pentecostes': 'Duhovi',
    'In Nativitate Domini': 'Božić — Rođenje Gospodina',
    'In Epiphania Domini': 'Bogojavljenje Gospodina',
    'In Ascensione Domini': 'Uzašašće Gospodina',
    'Ss.mi Corporis et Sanguinis Christi': 'Tijela i Krvi Kristove',
    'In Assumptione Beatæ Mariæ Virginis': 'Uznesenje Blažene Djevice Marije',
    'SOLLEMNITAS SANCTÆ DEI GENITRICIS MARIÆ': 'Marijino uzašašće',
    'Domini Nostri Iesu Christi Universorum Regis': 'Krista Kralja svega svijeta',
    'S. Familiæ Iesu, Mariæ et Joseph': 'Sveta obitelj',
    'In Conceptione Immaculata Beatæ Mariæ Virginis': 'Bezgrešno začeće Blažene Djevice Marije',
    'In Nativitate Sancti Ioannis Baptistæ': 'Rođenje sv. Ivana Krstitelja',
    'In Nativitate Beatæ Mariæ Virginis': 'Rođenje Blažene Djevice Marije',
    'Memoria Sanctæ Mariæ in Sabbato': 'Spomen Blažene Djevice Marije u subotu',
    'Dominica post Pentecostem Sanctissimæ Trinitatis': 'Presvetog Trojstva',
    'Vigilia Paschalis': 'Uskrsna vigilija',
    'Dominica in Palmis': 'Cvjetnica',
    'Feria IV Cinerum': 'Pepelnica',
    'Feria VI in Passione Domini': 'Veliki petak',
    'In Annuntiatione Domini': 'Navještaj Blažene Djevice Marije',
    'In Festo Baptismatis Domini': 'Krštenje Gospodina',
    'In Transfiguratione Domini': 'Preobraženje Gospodina',
    'Sacratissimi Cordis Iesu': 'Presvetog Srca Isusova',
    'In Commemoratione Omnium Fidelium Defunctorum': 'Dan svih vjernih pokojnika',
    'Sabbato infra Octavam Paschæ': 'Subota u oktavi Uskrsa',
}

# Zamjene uloga i fraza (duže prvo)
_PHRASES: list[tuple[str, str]] = [
    ('Missa in Vigilia', '(misa na vigiliji)'),
    ('Ecclesiæ doctoris', 'crkvenog učitelja'),
    ('Ecclesiæ doctorum', 'crkvenih učitelja'),
    ('Ecclesiæ doctor', 'crkveni učitelj'),
    ('apostolorum', 'apostola'),
    ('apostoli', 'apostola'),
    ('apostolorum Petri et Pauli', 'apostola Petra i Pavla'),
    ('presbyteri et martyris', 'prezbitera i mučenika'),
    ('episcopi et martyris', 'biskupa i mučenika'),
    ('episcopi', 'biskupa'),
    ('presbyteri', 'prezbitera'),
    ('diaconi', 'đakona'),
    ('diaconorum', 'đakona'),
    ('pontificis', 'pape'),
    ('martyris', 'mučenika'),
    ('martyrum', 'mučenika'),
    ('virginis', 'djevičke'),
    ('virginum', 'djevica'),
    ('confessoris', 'ispovjednika'),
    ('abbatis', 'opata'),
    ('regis', 'kralja'),
    ('reginæ', 'kraljice'),
    ('doctoris', 'učitelja'),
    ('doctorum', 'učitelja'),
    ('Temporis Ordinarii', 'običnog vremena'),
    ('Tempus per Annum', 'Obično vrijeme'),
    ('Tempus Adventus', 'Advent'),
    ('Tempus Quadragesimæ', 'Korizma'),
    ('Tempus Paschæ', 'Uskrsno razdoblje'),
    ('in Sabbato', 'u subotu'),
    ('Beatæ Mariæ Virginis', 'Blažene Djevice Marije'),
    ('Sanctæ Dei Genitricis Mariæ', 'Blažene Djevice Marije'),
    ('Domini Nostri', 'Gospodina našega'),
    ('Iesu Christi', 'Isusa Krista'),
    ('Sanctissimi', 'Presvetog'),
    ('Sanctissimæ', 'Presvete'),
    ('Sanctorum', 'svetaca'),
    ('Sanctorum ', 'svetih '),
    ('Sancti ', 'Sveti '),
    ('Sanctæ ', 'Sveta '),
    ('Sanctarum ', 'Sveta '),
    ('Beati ', 'Blazeni '),
    ('Beatæ ', 'Blazena '),
    ('Ss. ', 'Sv. '),
    ('S. ', 'Sv. '),
    (' et ', ' i '),
    (' vel ', ' ili '),
    (' in ', ' u '),
    (' de ', ' '),
    (' a ', ' '),
]

_LATIN_CHARS = str.maketrans({
    'æ': 'e', 'Æ': 'E',
    'œ': 'e', 'Œ': 'E',
    '«': '', '»': '',
})


def _roman_to_int(token: str) -> int | None:
    token = token.strip()
    low = token.lower()
    if low in _UNIT_ORD:
        return _UNIT_ORD[low]
    if low in _TENS_ORD:
        return _TENS_ORD[low]
    return _ROMAN.get(token)


def _parse_week_ordinal(phrase: str) -> int | None:
    """Latinski redni broj u genitivu (npr. Decimæ quartæ → 14)."""
    parts = phrase.strip().split()
    if not parts:
        return None
    if len(parts) == 1:
        return _roman_to_int(parts[0])
    if len(parts) == 2:
        tens = _TENS_ORD.get(parts[0].lower())
        unit = _UNIT_ORD.get(parts[1].lower())
        if tens is not None and unit is not None:
            return tens + unit
    return None


_SEASON_HR = {
    'Temporis Ordinarii': 'običnog vremena',
    'Temporis Paschali': 'uskrsnog vremena',
    'Quadragesimæ': 'korizme',
    'Adventus': 'adventa',
}


def _looks_latin(text: str) -> bool:
    if not text:
        return False
    markers = (
        'Dominica', 'Feria', 'Sanct', 'Beat', 'Temporis', 'Hebdomad',
        'Quadragesim', 'Adventus', 'Pasch', 'Pentecost', 'Nativitat',
        'Missa in Vigilia', 'Memoria', 'Octav',
    )
    return any(m in text for m in markers)


def _translate_dominica(name: str) -> str | None:
    base = name.replace(' Missa in Vigilia', '').strip()
    vigil = ' (misa na vigiliji)' if 'Missa in Vigilia' in name else ''

    if base in _EXACT:
        return _EXACT[base] + vigil

    ordinary_time_match = re.match(r'^Dominica\s+(.+?)\s+per annum$', base)
    if ordinary_time_match:
        sunday_number = _parse_week_ordinal(ordinary_time_match.group(1))
        if sunday_number is not None:
            return f'{sunday_number}. nedjelja kroz godinu{vigil}'

    m = re.match(r'^Dominica\s+(\S+)\s+(.+)$', base)
    if not m:
        return None
    num = _roman_to_int(m.group(1))
    season = m.group(2).strip().replace('«', '').replace('»', '').strip()
    if season.startswith('Adventus'):
        gaudete = ' (Gaudete)' if '(Gaudete)' in season else ''
        if num:
            return f'{num}. nedjelja adventa{gaudete}{vigil}'
    if season.startswith('Paschæ'):
        if num:
            return f'{num}. nedjelja uskrsnog vremena{vigil}'
    if num is None:
        return None
    if season == 'Adventus':
        return f'{num}. nedjelja adventa{vigil}'
    if season.startswith('in Paschæ'):
        if 'Misericordiæ' in season:
            return f'{num}. nedjelja uskrsta — Božje milosrđe{vigil}'
        return f'{num}. nedjelja uskrsta{vigil}'
    if season == 'in Quadragesima':
        return f'{num}. nedjelja korizmena{vigil}'
    if season == 'Post Nativitatem':
        return f'{num}. nedjelja po Božiću{vigil}'
    if season == 'Per Annum':
        return f'{num}. nedjelja u običnom vremenu{vigil}'
    return None


def _translate_feria(name: str) -> str | None:
    m = re.match(
        r'^Feria\s+(II|III|IV|V|VI)\s+Hebdomadæ\s+(.+?)\s+'
        r'(Temporis Ordinarii|Temporis Paschali|Quadragesimæ|Adventus)$',
        name,
    )
    if m:
        weekday = _WEEKDAY_FERIA.get(m.group(1), m.group(1))
        week = _parse_week_ordinal(m.group(2))
        season = _SEASON_HR.get(m.group(3), m.group(3))
        if week is not None:
            return f'{weekday} {week}. tjedna {season}'

    m2 = re.match(r'^Feria\s+(II|III|IV|V|VI)\s+temporis\s+Nativitatis$', name)
    if m2:
        weekday = _WEEKDAY_FERIA.get(m2.group(1), m2.group(1))
        return f'{weekday} božićnog razdoblja'

    m3 = re.match(r'^Feria\s+(II|III|IV|V|VI)\s+Hebdomadæ\s+Sanctæ$', name)
    if m3:
        weekday = _WEEKDAY_FERIA.get(m3.group(1), m3.group(1))
        return f'{weekday} svetog tjedna'

    m4 = re.match(r'^Feria\s+(II|III|IV|V|VI)\s+infra\s+Octavam\s+Paschæ$', name)
    if m4:
        weekday = _WEEKDAY_FERIA.get(m4.group(1), m4.group(1))
        return f'{weekday} u oktavi Uskrsa'

    m5 = re.match(r'^Feria\s+(II|III|IV|V|VI)\s+post\s+Feria\s+IV\s+Cinerum$', name)
    if m5:
        weekday = _WEEKDAY_FERIA.get(m5.group(1), m5.group(1))
        return f'{weekday} nakon Pepelnice'
    return None


def _translate_sabbato(name: str) -> str | None:
    m = re.match(
        r'^Sabbato\s+Hebdomadæ\s+(.+?)\s+(Adventus|Quadragesimæ)$',
        name,
    )
    if m:
        week = _parse_week_ordinal(m.group(1))
        season = _SEASON_HR.get(m.group(2), m.group(2))
        if week:
            return f'Subota {week}. tjedna {season}'
    if name == 'Sabbato temporis Nativitatis':
        return 'Subota božićnog razdoblja'
    if name == 'Sabbato post Feria IV Cinerum':
        return 'Subota nakon Pepelnice'
    m2 = re.match(
        r'^Sabbato\s+Hebdomadæ\s+(.+?)\s+Temporis\s+(Ordinarii|Paschali)$',
        name,
    )
    if m2:
        week = _parse_week_ordinal(m2.group(1))
        season = _SEASON_HR.get(f'Temporis {m2.group(2)}', m2.group(2))
        if week:
            return f'Subota {week}. tjedna {season}'
    return None


def _apply_phrases(text: str) -> str:
    out = text
    for lat, hr in _PHRASES:
        out = out.replace(lat, hr)
    return out.translate(_LATIN_CHARS).strip()


def translate_liturgical_name(
    name: str,
    *,
    allow_remote_translation: bool = True,
) -> tuple[str, bool]:
    """
    Vrati (hrvatski_naziv, uspješno_prijevodeno).
    Prvo offline rječnik, zatim deep-translator.
    """
    if not name or not str(name).strip():
        return name or '', False

    raw = str(name).strip()
    base = raw.replace(' Missa in Vigilia', '').strip()

    if base in _EXACT:
        suffix = ' (misa na vigiliji)' if 'Missa in Vigilia' in raw else ''
        return _EXACT[base] + suffix, True

    for handler in (_translate_dominica, _translate_feria, _translate_sabbato):
        result = handler(raw)
        if result:
            return result, True

    # Octava dani
    m = re.match(
        r'^Dies\s+(Quintus|Quartus|Sextus|Septimus)\s+Octavæ\s+Nativitatis$',
        base,
    )
    if m:
        day_map = {
            'Quintus': '5.', 'Quartus': '4.', 'Sextus': '6.', 'Septimus': '7.',
        }
        return f'{day_map[m.group(1)]} dan oktave Božića', True

    # Opći prijevod svetaca i ostalih naziva
    translated = _apply_phrases(raw)
    if translated != raw:
        hr_prefixes = ('Sveti ', 'Sveta ', 'Blazeni ', 'Blazena ', 'Sv. ', 'Spomen ')
        if translated.startswith(hr_prefixes):
            return translated, True
        if not _looks_latin(translated):
            return translated, True

    if allow_remote_translation:
        from liturgija.services.liturgical_deep import translate_to_hr

        remotely_translated_name = translate_to_hr(raw)
        if remotely_translated_name and remotely_translated_name != raw:
            return remotely_translated_name, True

    return raw, False


def translate_season_lcl(
    raw: str,
    *,
    allow_remote_translation: bool = True,
) -> str:
    if not raw:
        return ''
    key = str(raw).strip()
    seasons = {
        'Tempus Adventus': 'Advent',
        'Tempus Nativitatis': 'Božićno razdoblje',
        'Tempus Quadragesimæ': 'Korizma',
        'Tempus Paschæ': 'Uskrsno razdoblje',
        'Tempus Pentecostes': 'Duhovi',
        'Tempus per Annum': 'Obično vrijeme',
        'Tempus Post Pentecosten': 'Obično vrijeme',
    }
    if key in seasons:
        return seasons[key]
    translated_season, was_translated = translate_liturgical_name(
        key,
        allow_remote_translation=allow_remote_translation,
    )
    if was_translated:
        return translated_season
    if not allow_remote_translation:
        return key

    from liturgija.services.liturgical_deep import translate_to_hr

    return translate_to_hr(key)
