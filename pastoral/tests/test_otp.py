from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from pastoral.services.otp import dispatch_otp_email


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
