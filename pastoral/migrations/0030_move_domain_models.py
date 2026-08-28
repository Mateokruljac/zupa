# Generated manually — state-only move of domain models out of pastoral.

import django.db.models.deletion
from django.db import migrations, models
from django.db.migrations.operations.special import SeparateDatabaseAndState


def update_content_types(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    moves = [
        ('pastoral', 'liturgicaltradition', 'liturgija'),
        ('pastoral', 'liturgicalcalendarimport', 'liturgija'),
        ('pastoral', 'liturgicalcalendarentry', 'liturgija'),
        ('pastoral', 'churchsuiiuris', 'zupa_vjernici'),
        ('pastoral', 'ecclesiasticaljurisdiction', 'zupa_vjernici'),
        ('pastoral', 'person', 'zupa_vjernici'),
        ('pastoral', 'churchenrollment', 'zupa_vjernici'),
        ('pastoral', 'sacramentalevent', 'sakramenti'),
        ('pastoral', 'eventparticipant', 'sakramenti'),
        ('pastoral', 'baptismdetails', 'sakramenti'),
        ('pastoral', 'marriagedetails', 'sakramenti'),
        ('pastoral', 'funeraldetails', 'sakramenti'),
        ('pastoral', 'anointingdetails', 'sakramenti'),
        ('pastoral', 'formationprogramyear', 'sakramenti'),
        ('pastoral', 'formationcandidate', 'sakramenti'),
        ('pastoral', 'registertemplate', 'isprave'),
        ('pastoral', 'registertemplateversion', 'isprave'),
        ('pastoral', 'registerbook', 'isprave'),
        ('pastoral', 'registerbookyear', 'isprave'),
        ('pastoral', 'generalregisterentry', 'isprave'),
        ('pastoral', 'registerentry', 'isprave'),
        ('pastoral', 'registryauditevent', 'isprave'),
    ]
    for old_app, model, new_app in moves:
        ContentType.objects.filter(app_label=old_app, model=model).update(
            app_label=new_app,
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pastoral', '0028_harden_otp_challenges'),
        ('liturgija', '0001_move_domain_models'),
        ('zupa_vjernici', '0001_move_domain_models'),
        ('sakramenti', '0001_move_domain_models'),
        ('isprave', '0002_move_domain_models'),
    ]

    operations = [
        SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='parish',
                    name='church_sui_iuris',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='parishes',
                        to='zupa_vjernici.churchsuiiuris',
                        verbose_name='Crkva sui iuris',
                    ),
                ),
                migrations.AlterField(
                    model_name='parish',
                    name='ecclesiastical_jurisdiction',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='parishes',
                        to='zupa_vjernici.ecclesiasticaljurisdiction',
                        verbose_name='Crkvena jurisdikcija',
                    ),
                ),
                migrations.AlterField(
                    model_name='parish',
                    name='default_liturgical_tradition',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='parishes',
                        to='liturgija.liturgicaltradition',
                        verbose_name='Zadana liturgijska tradicija',
                    ),
                ),
                migrations.DeleteModel(name='AnointingDetails'),
                migrations.DeleteModel(name='BaptismDetails'),
                migrations.DeleteModel(name='MarriageDetails'),
                migrations.DeleteModel(name='FuneralDetails'),
                migrations.DeleteModel(name='EventParticipant'),
                migrations.DeleteModel(name='FormationCandidate'),
                migrations.DeleteModel(name='FormationProgramYear'),
                migrations.DeleteModel(name='RegisterEntry'),
                migrations.DeleteModel(name='GeneralRegisterEntry'),
                migrations.DeleteModel(name='RegisterBookYear'),
                migrations.DeleteModel(name='RegisterBook'),
                migrations.DeleteModel(name='RegisterTemplateVersion'),
                migrations.DeleteModel(name='RegisterTemplate'),
                migrations.DeleteModel(name='RegistryAuditEvent'),
                migrations.DeleteModel(name='SacramentalEvent'),
                migrations.DeleteModel(name='ChurchEnrollment'),
                migrations.DeleteModel(name='Person'),
                migrations.DeleteModel(name='EcclesiasticalJurisdiction'),
                migrations.DeleteModel(name='ChurchSuiIuris'),
                migrations.DeleteModel(name='LiturgicalCalendarEntry'),
                migrations.DeleteModel(name='LiturgicalCalendarImport'),
                migrations.DeleteModel(name='LiturgicalTradition'),
            ],
            database_operations=[
                migrations.RunPython(update_content_types, noop_reverse),
            ],
        ),
    ]
