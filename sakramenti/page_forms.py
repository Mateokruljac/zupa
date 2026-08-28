"""Priprema formi za stranice sakramenata."""
from __future__ import annotations

from sakramenti.forms import (
    AnointingForm,
    BaptismForm,
    ConfirmationCandidateForm,
    ConfirmationGroupForm,
    ConfirmationYearCreateForm,
    ConfirmationYearForm,
    FirstCommunionCandidateForm,
    FirstCommunionGroupForm,
    FirstCommunionYearCreateForm,
    FirstCommunionYearForm,
    FuneralForm,
    WeddingForm,
)

SACRAMENT_PAGE_SLUGS = frozenset({
    'krsenja',
    'vjencanja',
    'pogrebi',
    'pomazanje',
    'krizma',
    'prva-pricest',
})


def attach_sacrament_forms(page_slug: str, page_context: dict) -> bool:
    if page_slug not in SACRAMENT_PAGE_SLUGS:
        return False

    if page_slug == 'krizma':
        confirmation_group = page_context.get('confirmation', {})
        confirmation_year = page_context.get('conf_year')
        confirmation_years = page_context.get('conf_years') or [
            confirmation_year
        ]
        page_context['confirmation_year_form'] = ConfirmationYearForm(
            initial={'year': max(confirmation_years) + 1},
        )
        page_context['confirmation_year_create_form'] = (
            ConfirmationYearCreateForm(initial={
                'year': max(confirmation_years) + 1,
            })
        )
        page_context['confirmation_group_form'] = ConfirmationGroupForm(
            initial={
                'year': confirmation_year,
                'ceremony_date': confirmation_group.get('ceremonyDate'),
                'bishop': confirmation_group.get('bishop', ''),
                'group_fee': confirmation_group.get('groupFee', 0),
                'group_fee_paid': confirmation_group.get(
                    'groupFeePaid',
                    False,
                ),
            },
        )
        page_context['confirmation_candidate_form'] = (
            ConfirmationCandidateForm(initial={
                'year': confirmation_year,
                'status': 'priprema',
            })
        )
        return True

    if page_slug == 'prva-pricest':
        first_communion_group = page_context.get('fc_group', {})
        first_communion_year = page_context.get('fc_year')
        first_communion_years = page_context.get('fc_years') or [
            first_communion_year
        ]
        page_context['first_communion_year_form'] = FirstCommunionYearForm(
            initial={'year': max(first_communion_years) + 1},
        )
        page_context['first_communion_year_create_form'] = (
            FirstCommunionYearCreateForm(initial={
                'year': max(first_communion_years) + 1,
            })
        )
        page_context['first_communion_group_form'] = FirstCommunionGroupForm(
            initial={
                'year': first_communion_year,
                'group_name': first_communion_group.get('groupName', ''),
                'ceremony_date': first_communion_group.get('ceremonyDate'),
                'celebrant': first_communion_group.get('celebrant', ''),
                'group_fee': first_communion_group.get('groupFee', 0),
                'group_fee_paid': first_communion_group.get(
                    'groupFeePaid',
                    False,
                ),
            },
        )
        page_context['first_communion_candidate_form'] = (
            FirstCommunionCandidateForm(initial={
                'year': first_communion_year,
                'status': 'priprema',
            })
        )
        return True

    if page_slug == 'krsenja':
        page_context['baptism_form'] = BaptismForm()
    elif page_slug == 'vjencanja':
        page_context['wedding_form'] = WeddingForm()
    elif page_slug == 'pogrebi':
        page_context['funeral_form'] = FuneralForm()
    elif page_slug == 'pomazanje':
        page_context['anointing_form'] = AnointingForm()
    return True
