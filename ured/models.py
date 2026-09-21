"""Operativni zapisi župnog ureda.

Kalendar, zadaci, javne prijave, vijeća i osnivački dekret.
Prava korisnika nisu ovdje — Django groups i `ParishMembership`.
Dokumenti ostaju otvoreno pitanje (`DocumentBinding` nije DMS).
"""
from core.models import FCTA, SCD1, SCD2, current_version_unique
from django.db import models


class OfficeTask(FCTA):
    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='office_tasks',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=40, blank=True, default='srednja')
    is_done = models.BooleanField(default=False)
    category = models.CharField(max_length=80, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]


class ParishCalendarEvent(FCTA):
    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='calendar_events',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    event_date = models.DateField(null=True, blank=True)
    place = models.CharField(max_length=160, blank=True)
    event_type = models.CharField(max_length=80, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]


class PublicSubmission(FCTA):
    class FormType(models.TextChoices):
        BAPTISM = 'baptism', 'Krštenje'
        FIRST_COMMUNION = 'first_communion', 'Prva pričest'
        CONFIRMATION = 'confirmation', 'Krizma'
        MARRIAGE = 'marriage', 'Vjenčanje'
        FUNERAL = 'funeral', 'Sprovod'

    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Poslano'
        UNDER_REVIEW = 'under_review', 'U obradi'
        APPROVED = 'approved', 'Odobreno'
        CONVERTED = 'converted', 'Prevedeno'
        REJECTED = 'rejected', 'Odbijeno'
        CANCELLED = 'cancelled', 'Otkazano'

    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='public_submissions',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    form_type = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=40, blank=True)
    person_name = models.CharField(max_length=160, blank=True)
    phone = models.CharField(max_length=64, blank=True)
    email = models.CharField(max_length=160, blank=True)
    address = models.CharField(max_length=255, blank=True)
    submitted_at = models.CharField(max_length=64, blank=True)
    form_data = models.JSONField(default=dict, blank=True)
    extra = models.JSONField(default=dict, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    converted_person = models.ForeignKey(
        'zupa_vjernici.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_public_submissions',
    )
    converted_event = models.ForeignKey(
        'sakramenti.SacramentalEvent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_public_submissions',
    )
    converted_candidate = models.ForeignKey(
        'sakramenti.FormationCandidate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_public_submissions',
    )

    class Meta:
        unique_together = [('parish', 'public_identifier')]


class Announcement(FCTA):
    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='announcements',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    announced_at = models.CharField(max_length=64, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]


class Council(SCD1):
    """Župno pastoralno ili ekonomsko vijeće.

    Jedan red po vrsti u župi. Članovi nisu JSON — to je `CouncilMembership`.
    Termini sastanaka ovdje su operativni datumi, ne kalendarski događaji.
    """

    unified_key_origin_fields = ('parish_id', 'council_type')

    class CouncilType(models.TextChoices):
        PASTORAL = 'pastoral', 'Pastoralno vijeće'
        ECONOMIC = 'economic', 'Ekonomsko vijeće'

    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='councils',
    )
    council_type = models.CharField(max_length=20, choices=CouncilType.choices)
    title = models.CharField(max_length=220, blank=True)
    established_on = models.DateField(null=True, blank=True)
    last_meeting_on = models.DateField(null=True, blank=True)
    next_meeting_on = models.DateField(null=True, blank=True)
    budget_year = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = [('parish', 'council_type')]
        verbose_name = 'Vijeće'
        verbose_name_plural = 'Vijeća'

    def __str__(self):
        return self.title or self.get_council_type_display()


class CouncilMembership(SCD2):
    """Mandat osobe (ili povijesnog imena) u vijeću.

    Nije Django Group niti pravo na modul. Prava ureda idu kroz groups
    i `ParishMembership`.
    """
    unified_key_origin_fields = ('council_id', 'public_identifier')

    council = models.ForeignKey(
        Council,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    person = models.ForeignKey(
        'zupa_vjernici.Person',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='council_memberships',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    member_name = models.CharField(max_length=220, blank=True)
    role = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=64, blank=True)
    is_confirmed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = (
            current_version_unique(
                'council',
                'public_identifier',
                name='councilmembership_one_current_id',
            ),
        )
        verbose_name = 'Članstvo u vijeću'
        verbose_name_plural = 'Članstva u vijeću'


class ParishFoundingDecree(SCD1):
    """Kanonski identitet župe (naziv, teritorij, referenca dekreta).

    Nije DMS i ne drži datoteke. Pitanje spremanja isprava ostaje otvoreno.
    """

    unified_key_origin_fields = ('parish_id',)

    parish = models.OneToOneField(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='founding_decree',
    )
    official_name = models.CharField(max_length=220, blank=True)
    established_text = models.CharField(max_length=80, blank=True)
    territory = models.CharField(max_length=255, blank=True)
    decree_reference = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Osnivački dekret župe'
        verbose_name_plural = 'Osnivački dekreti župa'

    def __str__(self):
        return self.official_name or str(self.parish_id)


class DocumentBinding(FCTA):
    parish = models.ForeignKey(
        'pastoral.Parish',
        on_delete=models.CASCADE,
        related_name='document_bindings',
    )
    public_identifier = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('parish', 'public_identifier')]
