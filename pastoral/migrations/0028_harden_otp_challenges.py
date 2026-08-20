from django.db import migrations, models

import pastoral.models


def invalidate_legacy_plaintext_challenges(apps, schema_editor):
    otp_challenge_model = apps.get_model('pastoral', 'OtpChallenge')
    otp_challenge_model.objects.update(
        code='!legacy-invalidated',
        used=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ('pastoral', '0027_cutover_general_register_entries_to_relational'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otpchallenge',
            name='code',
            field=models.CharField(max_length=128),
        ),
        migrations.AddField(
            model_name='otpchallenge',
            name='expires_at',
            field=models.DateTimeField(
                db_index=True,
                default=pastoral.models.otp_challenge_expiry,
            ),
        ),
        migrations.AddField(
            model_name='otpchallenge',
            name='failed_attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='otpchallenge',
            name='locked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(
            invalidate_legacy_plaintext_challenges,
            migrations.RunPython.noop,
        ),
    ]
