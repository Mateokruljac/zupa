from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, SimpleTestCase

from pastoral.actions import handle_page_post
from pastoral.page_actions.councils import handle_council_action
from pastoral.page_actions.families import handle_family_action
from pastoral.page_actions.formation import handle_formation_action
from pastoral.page_actions import dispatcher
from pastoral.page_actions.operations import handle_operations_action


class RecordingParishDataService:
    def __init__(self, parish_data=None):
        self.parish_data = parish_data or {}
        self.load_count = 0
        self.saved_parish_data = None

    def load(self):
        self.load_count += 1
        return self.parish_data

    def save(self, parish_data):
        self.saved_parish_data = parish_data


def build_post_request(post_data):
    request = RequestFactory().post('/app/test/', post_data)
    request.session = {}
    request._messages = FallbackStorage(request)
    request.user = SimpleNamespace(name='Župnik', email='zupnik@example.test')
    return request


class PageActionDispatcherTests(SimpleTestCase):
    def test_does_not_load_parish_data_when_action_is_missing(self):
        request = build_post_request({})
        parish_data_service = RecordingParishDataService()

        action_was_handled = handle_page_post(
            request,
            'nakane',
            parish_data_service,
        )

        self.assertFalse(action_was_handled)
        self.assertEqual(parish_data_service.load_count, 0)

    def test_stops_after_first_handler_that_accepts_action(self):
        request = build_post_request({'action': 'test_action'})
        parish_data_service = RecordingParishDataService({'tasks': []})
        called_handlers = []

        def ignored_action_handler(*arguments):
            called_handlers.append('ignored')
            return False

        def accepting_action_handler(*arguments):
            called_handlers.append('accepted')
            return True

        def unreachable_action_handler(*arguments):
            called_handlers.append('unreachable')
            return True

        action_handlers = (
            ignored_action_handler,
            accepting_action_handler,
            unreachable_action_handler,
        )
        with patch.object(dispatcher, 'PAGE_ACTION_HANDLERS', action_handlers):
            action_was_handled = handle_page_post(
                request,
                'nakane',
                parish_data_service,
            )

        self.assertTrue(action_was_handled)
        self.assertEqual(called_handlers, ['ignored', 'accepted'])
        self.assertEqual(parish_data_service.load_count, 1)


class OperationsActionTests(SimpleTestCase):
    def test_updates_allowed_operational_item_status(self):
        request = build_post_request({
            'action': 'update_operation_status',
            'collection': 'facilityTasks',
            'source_id': 'facility-1',
            'status': 'completed',
        })
        parish_data = {
            'facilityTasks': [{'id': 'facility-1', 'status': 'open'}],
        }
        parish_data_service = RecordingParishDataService(parish_data)

        action_was_handled = handle_operations_action(
            request,
            'operativno-srediste',
            'update_operation_status',
            parish_data,
            parish_data_service,
        )

        self.assertTrue(action_was_handled)
        self.assertEqual(parish_data['facilityTasks'][0]['status'], 'completed')
        self.assertIs(parish_data_service.saved_parish_data, parish_data)


class CouncilActionTests(SimpleTestCase):
    def test_adds_member_without_changing_existing_council_schema(self):
        request = build_post_request({
            'action': 'add_council_member',
            'council_type': 'pastoral',
            'name': 'Marija Primjer',
            'role': 'članica',
            'confirmed': 'on',
        })
        parish_data = {
            'pastoralCouncil': {
                'nextMeeting': '2026-09-01',
                'members': [],
            },
        }
        parish_data_service = RecordingParishDataService(parish_data)

        action_was_handled = handle_council_action(
            request,
            'vijeca',
            'add_council_member',
            parish_data,
            parish_data_service,
        )

        self.assertTrue(action_was_handled)
        self.assertEqual(
            parish_data['pastoralCouncil']['nextMeeting'],
            '2026-09-01',
        )
        new_member = parish_data['pastoralCouncil']['members'][0]
        self.assertEqual(new_member['name'], 'Marija Primjer')
        self.assertEqual(new_member['role'], 'članica')
        self.assertTrue(new_member['confirmed'])
        self.assertTrue(new_member['id'].startswith('zpv-'))

    def test_schedules_economic_council_review_using_existing_key(self):
        request = build_post_request({
            'action': 'schedule_council_meeting',
            'council_type': 'economic',
            'meeting_date': '2026-10-15',
        })
        parish_data = {'economicCouncil': {'members': []}}
        parish_data_service = RecordingParishDataService(parish_data)

        action_was_handled = handle_council_action(
            request,
            'vijeca',
            'schedule_council_meeting',
            parish_data,
            parish_data_service,
        )

        self.assertTrue(action_was_handled)
        self.assertEqual(
            parish_data['economicCouncil']['nextReview'],
            '2026-10-15',
        )

    def test_toggles_only_selected_member_confirmation(self):
        request = build_post_request({
            'action': 'toggle_council_member_confirmation',
            'council_type': 'pastoral',
            'member_id': 'member-1',
        })
        parish_data = {
            'pastoralCouncil': {
                'members': [
                    {'id': 'member-1', 'confirmed': False},
                    {'id': 'member-2', 'confirmed': True},
                ],
            },
        }
        parish_data_service = RecordingParishDataService(parish_data)

        handle_council_action(
            request,
            'vijeca',
            'toggle_council_member_confirmation',
            parish_data,
            parish_data_service,
        )

        self.assertTrue(parish_data['pastoralCouncil']['members'][0]['confirmed'])
        self.assertTrue(parish_data['pastoralCouncil']['members'][1]['confirmed'])


class FormationActionTests(SimpleTestCase):
    def test_saves_confirmation_group_independently_from_candidates(self):
        request = build_post_request({
            'action': 'save_confirmation_group',
            'year': '2026',
            'ceremony_date': '2026-10-07',
            'bishop': 'Nadbiskup',
            'group_fee': '45.00',
            'group_fee_paid': 'on',
        })
        parish_data = {
            'confirmations': [
                {'year': 2026, 'candidates': [{'id': 'candidate-1'}]},
            ],
        }
        parish_data_service = RecordingParishDataService(parish_data)

        action_was_handled = handle_formation_action(
            request,
            'krizma',
            'save_confirmation_group',
            parish_data,
            parish_data_service,
        )

        self.assertTrue(action_was_handled)
        confirmation_group = parish_data['confirmations'][0]
        self.assertEqual(confirmation_group['bishop'], 'Nadbiskup')
        self.assertEqual(confirmation_group['ceremonyDate'], '2026-10-07')
        self.assertEqual(confirmation_group['candidates'], [{'id': 'candidate-1'}])

    def test_adds_first_communion_candidate_to_selected_year(self):
        request = build_post_request({
            'action': 'add_first_communion_candidate',
            'year': '2026',
            'first_name': 'Ema',
            'last_name': 'Horvat',
            'school': 'OŠ Primjer',
            'school_class': '4.a',
            'parents': 'Ana i Ivan Horvat',
            'status': 'priprema',
        })
        parish_data = {
            'firstCommunion': [{'year': 2026, 'candidates': []}],
        }
        parish_data_service = RecordingParishDataService(parish_data)

        handle_formation_action(
            request,
            'prva-pricest',
            'add_first_communion_candidate',
            parish_data,
            parish_data_service,
        )

        candidate = parish_data['firstCommunion'][0]['candidates'][0]
        self.assertEqual(candidate['name'], 'Ema Horvat')
        self.assertEqual(candidate['class'], '4.a')


class FamilyActionTests(SimpleTestCase):
    def test_adds_basic_family_card_using_existing_schema(self):
        request = build_post_request({
            'action': 'add_family',
            'surname': 'Kovač',
            'street_id': 'street-1',
            'address': 'Testna 12',
            'phone': '091 123 456',
            'email': 'obitelj@example.test',
            'origin_place': 'Zagreb',
        })
        parish_data = {
            'streets': [{'id': 'street-1', 'name': 'Testna'}],
            'families': [],
        }
        parish_data_service = RecordingParishDataService(parish_data)

        handle_family_action(
            request,
            'obitelji',
            'add_family',
            parish_data,
            parish_data_service,
        )

        family = parish_data['families'][0]
        self.assertEqual(family['surname'], 'Kovač')
        self.assertEqual(family['streetId'], 'street-1')
        self.assertEqual(family['members'], [])

    def test_saves_lukno_and_church_donation_for_family(self):
        request = build_post_request({
            'action': 'save_family_contribution',
            'family_id': 'family-1',
            'year': '2026',
            'lukno_amount': '160.00',
            'lukno_paid': 'on',
            'lukno_paid_at': '2026-03-01',
            'church_donation': '50.00',
            'donation_date': '2026-03-15',
            'notes': 'Uskrsni dar',
        })
        parish_data = {
            'families': [{
                'id': 'family-1',
                'surname': 'Horvat',
                'contributions': [],
            }],
        }
        parish_data_service = RecordingParishDataService(parish_data)

        handle_family_action(
            request,
            'obitelji',
            'save_family_contribution',
            parish_data,
            parish_data_service,
        )

        contribution = parish_data['families'][0]['contributions'][0]
        self.assertEqual(contribution['year'], 2026)
        self.assertEqual(contribution['luknoAmount'], 160.0)
        self.assertTrue(contribution['luknoPaid'])
        self.assertEqual(contribution['luknoPaidAt'], '2026-03-01')
        self.assertEqual(contribution['churchDonation'], 50.0)
        self.assertEqual(contribution['donationDate'], '2026-03-15')
        self.assertEqual(contribution['notes'], 'Uskrsni dar')
        self.assertIs(parish_data_service.saved_parish_data, parish_data)
