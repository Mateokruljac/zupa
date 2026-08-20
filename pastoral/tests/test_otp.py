from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.hashers import check_password
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from pastoral.models import OtpChallenge
from pastoral.services.otp import (
    OtpCooldownError,
    create_otp_challenge,
    dispatch_otp_email,
    request_otp_delivery,
    verify_otp_challenge,
)


class OtpEmailDispatchTests(SimpleTestCase):
    @override_settings(OTP_RECIPIENT='otp-recipient@example.test')
    @patch('pastoral.services.otp.ParishDataService')
    @patch(
        'pastoral.services.otp.send_otp_email_task.delay',
        side_effect=ConnectionError('Redis nije dostupan'),
    )
    def test_returns_controlled_error_when_task_cannot_be_queued(
        self,
        send_email_task,
        parish_data_service_class,
    ):
        parish_data_service = parish_data_service_class.return_value
        parish_data_service.load_settings.return_value = {}

        email_was_sent, email_result = dispatch_otp_email(
            '123456',
            'user@example.test',
            'zupnik',
        )

        self.assertFalse(email_was_sent)
        self.assertEqual(email_result['error'], 'mail_queue_unavailable')
        self.assertEqual(
            email_result['recipient'],
            'otp-recipient@example.test',
        )
        send_email_task.assert_called_once()
        parish_data_service_class.assert_called_once_with()
        parish_data_service.load_settings.assert_called_once_with()

    @patch('pastoral.services.otp.invalidate_latest_otp_challenge')
    @patch('pastoral.services.otp.dispatch_otp_email')
    @patch('pastoral.services.otp.create_otp_challenge', return_value='123456')
    def test_delivery_stores_pending_session_only_after_success(
        self,
        create_challenge,
        dispatch_email,
        invalidate_challenge,
    ):
        dispatch_email.return_value = (True, {'ok': True, 'recipient': 'otp@example.test'})
        request = SimpleNamespace(session={})

        delivery_result = request_otp_delivery(
            request,
            email='USER@example.test',
            role='zupnik',
        )

        self.assertEqual(delivery_result[0], True)
        self.assertEqual(
            request.session['otp_pending'],
            {'email': 'USER@example.test', 'role': 'zupnik'},
        )
        create_challenge.assert_called_once_with('USER@example.test', 'zupnik')
        dispatch_email.assert_called_once_with(
            '123456',
            'USER@example.test',
            'zupnik',
            timeout=20,
        )
        invalidate_challenge.assert_not_called()

    @patch('pastoral.services.otp.invalidate_latest_otp_challenge')
    @patch(
        'pastoral.services.otp.dispatch_otp_email',
        return_value=(False, {'error': 'send_failed'}),
    )
    @patch('pastoral.services.otp.create_otp_challenge', return_value='123456')
    def test_delivery_invalidates_challenge_when_email_fails(
        self,
        create_challenge,
        dispatch_email,
        invalidate_challenge,
    ):
        request = SimpleNamespace(session={})

        delivery_result = request_otp_delivery(
            request,
            email='user@example.test',
            role='zupnik',
        )

        self.assertEqual(delivery_result, (False, {'error': 'send_failed'}))
        self.assertNotIn('otp_pending', request.session)
        invalidate_challenge.assert_called_once_with('user@example.test', 'zupnik')


@override_settings(
    OTP_TTL_MINUTES=10,
    OTP_MAX_ATTEMPTS=5,
    OTP_RESEND_COOLDOWN_SECONDS=60,
)
class OtpChallengeSecurityTests(TestCase):
    email_address = 'user@example.test'
    user_role = 'zupnik'

    @patch('pastoral.services.otp.secrets.randbelow', return_value=123456)
    def test_stores_only_a_salted_hash(self, random_number):
        verification_code = create_otp_challenge(
            self.email_address,
            self.user_role,
        )

        challenge = OtpChallenge.objects.get()
        self.assertEqual(verification_code, '123456')
        self.assertNotEqual(challenge.code, verification_code)
        self.assertTrue(check_password(verification_code, challenge.code))
        random_number.assert_called_once_with(1_000_000)

    @override_settings(OTP_RESEND_COOLDOWN_SECONDS=0)
    def test_successful_code_can_be_used_only_once(self):
        verification_code = create_otp_challenge(
            self.email_address,
            self.user_role,
        )

        first_result = verify_otp_challenge(
            self.email_address,
            self.user_role,
            verification_code,
        )
        second_result = verify_otp_challenge(
            self.email_address,
            self.user_role,
            verification_code,
        )

        self.assertEqual(first_result, (True, 'verified'))
        self.assertEqual(second_result, (False, 'missing'))

    def test_expired_code_is_rejected(self):
        verification_code = create_otp_challenge(
            self.email_address,
            self.user_role,
        )
        OtpChallenge.objects.update(expires_at=timezone.now())

        result = verify_otp_challenge(
            self.email_address,
            self.user_role,
            verification_code,
        )

        self.assertEqual(result, (False, 'expired'))
        self.assertTrue(OtpChallenge.objects.get().used)

    @patch('pastoral.services.otp.secrets.randbelow', return_value=999999)
    def test_challenge_is_locked_after_five_wrong_attempts(self, random_number):
        create_otp_challenge(self.email_address, self.user_role)

        for attempt_number in range(5):
            result = verify_otp_challenge(
                self.email_address,
                self.user_role,
                f'{attempt_number:06d}',
            )

        challenge = OtpChallenge.objects.get()
        self.assertEqual(result, (False, 'locked'))
        self.assertEqual(challenge.failed_attempts, 5)
        self.assertTrue(challenge.used)
        self.assertIsNotNone(challenge.locked_at)
        random_number.assert_called_once_with(1_000_000)

    def test_repeated_request_during_cooldown_is_rejected(self):
        create_otp_challenge(self.email_address, self.user_role)

        with self.assertRaises(OtpCooldownError):
            create_otp_challenge(self.email_address, self.user_role)
