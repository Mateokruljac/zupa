from unittest.mock import patch

from django.test import SimpleTestCase

from pastoral.services import api_actions


class RecordingParishDataService:
    def __init__(self):
        self.parish_data = {'families': []}
        self.parish_settings = {'name': 'Testna župa'}
        self.load_count = 0
        self.save_count = 0

    def load(self):
        self.load_count += 1
        return self.parish_data

    def load_settings(self):
        return self.parish_settings

    def save(self, parish_data):
        self.save_count += 1
        self.parish_data = parish_data


class ApiActionDispatcherTests(SimpleTestCase):
    def test_unknown_action_does_not_load_parish_data(self):
        parish_data_service = RecordingParishDataService()

        action_result = api_actions.dispatch_action(
            'unknown_test_action',
            {},
            parish_data_service,
        )

        self.assertEqual(action_result, {
            'ok': False,
            'error': 'unknown_action',
            'action': 'unknown_test_action',
        })
        self.assertEqual(parish_data_service.load_count, 0)

    def test_read_only_action_receives_settings_without_saving(self):
        parish_data_service = RecordingParishDataService()

        def read_only_handler(parish_data, action_payload, parish_settings):
            return {
                'ok': True,
                'parish': parish_settings['name'],
                'requested': action_payload['requested'],
            }

        with (
            patch.object(
                api_actions,
                'ACTION_HANDLERS',
                {'test_read_only': read_only_handler},
            ),
            patch.object(
                api_actions,
                'READ_ONLY_ACTION_NAMES',
                frozenset({'test_read_only'}),
            ),
            patch.object(
                api_actions,
                'SETTINGS_AWARE_ACTION_NAMES',
                frozenset({'test_read_only'}),
            ),
            patch.object(
                api_actions,
                'normalize_parish_data',
                lambda parish_data: parish_data,
            ),
        ):
            action_result = api_actions.dispatch_action(
                'test_read_only',
                {'requested': 'pregled'},
                parish_data_service,
            )

        self.assertEqual(action_result, {
            'ok': True,
            'parish': 'Testna župa',
            'requested': 'pregled',
        })
        self.assertEqual(parish_data_service.save_count, 0)

    def test_mutating_action_saves_and_preserves_response_contract(self):
        parish_data_service = RecordingParishDataService()

        def mutating_handler(parish_data, action_payload):
            parish_data['savedValue'] = action_payload['value']
            return {'ok': True, 'item': {'value': action_payload['value']}}

        with (
            patch.object(
                api_actions,
                'ACTION_HANDLERS',
                {'test_mutation': mutating_handler},
            ),
            patch.object(
                api_actions,
                'READ_ONLY_ACTION_NAMES',
                frozenset(),
            ),
            patch.object(
                api_actions,
                'SETTINGS_AWARE_ACTION_NAMES',
                frozenset(),
            ),
            patch.object(
                api_actions,
                'normalize_parish_data',
                lambda parish_data: parish_data,
            ),
        ):
            action_result = api_actions.dispatch_action(
                'test_mutation',
                {'value': 'spremljeno'},
                parish_data_service,
            )

        self.assertTrue(action_result['ok'])
        self.assertEqual(action_result['data']['savedValue'], 'spremljeno')
        self.assertEqual(action_result['item'], {'value': 'spremljeno'})
        self.assertEqual(parish_data_service.save_count, 1)
