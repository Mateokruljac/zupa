"""Kategorije uplata obitelji (lukno, dar, zvonarina, ostalo)."""
from __future__ import annotations

from zupa_vjernici.models import HouseholdContribution

CONTRIBUTION_CATEGORY_LABELS = dict(HouseholdContribution.CATEGORY_CHOICES)
LUKNO_CATEGORY = HouseholdContribution.CATEGORY_LUKNO


def normalize_contribution_category(value: str | None) -> str:
    category = (value or '').strip()
    if category in CONTRIBUTION_CATEGORY_LABELS:
        return category
    return LUKNO_CATEGORY


def is_lukno_contribution(contribution: dict) -> bool:
    return normalize_contribution_category(
        contribution.get('category'),
    ) == LUKNO_CATEGORY


def contribution_category_label(category: str | None) -> str:
    normalized = normalize_contribution_category(category)
    return CONTRIBUTION_CATEGORY_LABELS.get(normalized, normalized)


def _category_rows(by_category: dict[str, float]) -> list[dict]:
    return [
        {
            'category': category,
            'label': contribution_category_label(category),
            'total': round(total, 2),
        }
        for category, total in sorted(
            by_category.items(),
            key=lambda item: contribution_category_label(item[0]),
        )
    ]


def contribution_totals(contributions: list[dict] | None) -> dict:
    """Zbrojevi uplata po godini i po kategoriji."""
    by_year: dict[int, float] = {}
    by_year_category: dict[int, dict[str, float]] = {}
    by_category: dict[str, float] = {}
    grand_total = 0.0
    for contribution in contributions or []:
        if not isinstance(contribution, dict):
            continue
        try:
            amount = float(contribution.get('luknoAmount') or 0)
        except (TypeError, ValueError):
            amount = 0.0
        if amount == 0:
            continue
        try:
            year = int(contribution.get('year') or 0)
        except (TypeError, ValueError):
            year = 0
        category = normalize_contribution_category(contribution.get('category'))
        if year:
            by_year[year] = by_year.get(year, 0.0) + amount
            year_categories = by_year_category.setdefault(year, {})
            year_categories[category] = year_categories.get(category, 0.0) + amount
        by_category[category] = by_category.get(category, 0.0) + amount
        grand_total += amount
    return {
        'byYear': [
            {
                'year': year,
                'total': round(total, 2),
                'byCategory': _category_rows(by_year_category.get(year, {})),
            }
            for year, total in sorted(by_year.items(), reverse=True)
        ],
        'byCategory': _category_rows(by_category),
        'grandTotal': round(grand_total, 2),
    }


def parish_contribution_totals(families: list[dict] | None) -> dict:
    """Zbroj svih uplata u župi (homepage obitelji)."""
    all_contributions: list[dict] = []
    for family in families or []:
        if not isinstance(family, dict):
            continue
        contributions = family.get('contributions')
        if isinstance(contributions, list):
            all_contributions.extend(
                item for item in contributions if isinstance(item, dict)
            )
    return contribution_totals(all_contributions)
