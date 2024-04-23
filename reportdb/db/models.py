import reversion
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse


def publication_upload_path(instance, filename):
    return f"pub/{instance.pk}/{filename}"


@reversion.register()
class Publication(models.Model):
    name = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    public = models.BooleanField(default=False)
    text_file = models.FileField(
        upload_to=publication_upload_path, blank=True, null=True
    )
    pdf_file = models.FileField(
        upload_to=publication_upload_path,
        verbose_name="PDF file",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("db:publication_detail", kwargs={"publication_id": self.pk})

    def get_pdf_url(self) -> str:
        if self.pdf_file:
            return self.pdf_file.url
        return ""

    def get_text_url(self) -> str:
        if self.text_file:
            return f"{settings.STATIC_URL}aca/{self.name}.txt"
        return ""

    def get_text_path(self):
        return f"{settings.STATIC_ROOT}/aca/{self.name}.txt"


class IncidentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("publication")

    def public(self):
        return self.get_queryset().filter(publication__public=True)

    def approved(self):
        return self.public().filter(approved=True)

    def pending(self):
        return (
            self.public()
            .filter(approved=False)
            .exclude(Q(incident_report="") | Q(incident_report__isnull=True))
        )

    def need_report_text(self):
        return self.public().filter(
            Q(incident_report="") | Q(incident_report__isnull=True)
        )

    def need_analysis(self):
        return (
            self.approved()
            .filter(Q(incident_analysis="") | Q(incident_analysis__isnull=True))
            .filter(no_analysis=False)
        )

    def need_review(self):
        return self.public().exclude(editing_notes="")


@reversion.register()
class Incident(models.Model):
    class DataInput(models.TextChoices):
        UNKNOWN = "YY", "Unknown"
        HUMAN = "HU", "Human"
        AI = "AI", "AI"

    class PrimaryType(models.TextChoices):
        UNKNOWN = "YY", "Unknown"
        ROCKFALL = "B", "Rockfall"
        STUCK = "C", "Stuck"
        LOST = "D", "Lost"
        STRANDED = "E", "Stranded"
        ROPE = "F", "Difficulty on rope"
        LADDER = "G", "Difficulty on ladder"
        EQUIPMENT = "H", "Equipment problems"
        HYPOTHERMIA = "I", "Hypothermia"
        RAPPEL = "J", "Lost control on rappel"
        RIGGING = "K", "Rigging problems"
        FALL = "L", "Caver fall"
        DROWNING = "M", "Drowning"
        ACETYLENE = "N", "Acetylene related"
        AIR = "O", "Bad air"
        ILLNESS = "P", "Illness"
        INJURY = "Q", "Injury that does not fit other categories"

    class SecondaryType(models.TextChoices):
        NONE = "XX", "None"
        ROCKFALL = "B", "Rockfall"
        STUCK = "C", "Stuck"
        LOST = "D", "Lost"
        STRANDED = "E", "Stranded"
        ROPE = "F", "Difficulty on rope"
        LADDER = "G", "Difficulty on ladder"
        EQUIPMENT = "H", "Equipment problems"
        HYPOTHERMIA = "I", "Hypothermia"
        RAPPEL = "J", "Lost control on rappel"
        RIGGING = "K", "Rigging problems"
        FALL = "L", "Caver fall"
        DROWNING = "M", "Drowning"
        ACETYLENE = "N", "Acetylene related"
        AIR = "O", "Bad air"
        ILLNESS = "P", "Illness"
        INJURY = "Q", "Injury that does not fit other categories"

    class Category(models.TextChoices):
        UNKNOWN = "YY", "Unknown"
        CAVING = "CA", "Caving"
        CAVING_RELATED = "CR", "Caving related"
        DIVING = "CD", "Cave diving"
        OTHER = "ZZ", "Other"

    class AidType(models.TextChoices):
        UNKNOWN = "YY", "Unknown"
        NONE = "XX", "None"
        SURFACE = "SU", "Surface aid"
        UNDERGROUND = "UN", "Underground aid"
        RECOVERY = "RE", "Body recovery"
        STANDBY = "ST", "Aid on standby"
        OTHER = "ZZ", "Other"

    class GroupType(models.TextChoices):
        UNKNOWN = "YY", "Unknown"
        CAVERS = "CA", "Cavers"
        NOVICES = "NO", "Novice cavers"
        COLLEGE = "CO", "College cavers"
        CLUB = "CL", "Club or grotto cavers"
        NONCAVERS = "NC", "Non-cavers"
        DIVERS = "DI", "Cave divers"
        INDUSTRY = "IN", "Industrial"
        MILITARY = "MI", "Military"
        OTHER = "ZZ", "Other"

    class Source(models.TextChoices):
        UNKNOWN = "YY", "Unknown"
        INJURED_CAVER = "CA", "Injured caver"
        CAVER_IN_PARTY = "PA", "Member of injured caver's party"
        RESCUER = "RE", "Member of rescue party"
        THIRD_PARTY = "TH", "Third party"

    date = models.DateField(
        help_text=(
            "The date that the incident occurred. If you do not know the exact date, "
            "use the first of the month, or year, then tick 'Approximate date'."
        )
    )
    approximate_date = models.BooleanField(
        default=False,
        help_text="Tick this box if the date above is approximate.",
    )
    publication = models.ForeignKey(
        Publication,
        on_delete=models.PROTECT,
        related_name="incidents",
        help_text="The publication that this incident appeared in.",
    )
    publication_page = models.IntegerField(
        help_text=(
            "The page number that this incident appeared on in the publication. "
            "This should be taken from the page number in the corner of the PDF."
        ),
        validators=[MinValueValidator(1)],
        blank=True,
    )
    cave = models.CharField(max_length=100, help_text="If not known, enter 'unknown'.")
    state = models.CharField(
        max_length=50, blank=True, help_text="Use the full name of the state."
    )
    county = models.CharField(
        max_length=50,
        blank=True,
        help_text="Use the full name of the county.",
    )
    country = models.CharField(
        max_length=50,
        default="USA",
        help_text="Use 'USA', not 'United States of America'.",
    )
    category = models.CharField(
        max_length=2,
        choices=Category.choices,
        default=Category.UNKNOWN,
        help_text="Select the category that best describes the incident.",
    )
    incident_type = models.CharField(
        "primary type",
        max_length=2,
        help_text="The primary type of the incident.",
        choices=PrimaryType.choices,
        default=PrimaryType.UNKNOWN,
    )
    incident_type_2 = models.CharField(
        "Secondary type",
        max_length=2,
        help_text="If the incident fits a second type category, enter it here.",
        choices=SecondaryType.choices,
        default=SecondaryType.NONE,
    )
    incident_type_3 = models.CharField(
        "Tertiary type",
        max_length=2,
        help_text="If the incident fits a third type category, enter it here.",
        choices=SecondaryType.choices,
        default=SecondaryType.NONE,
    )
    primary_cause = models.CharField(
        max_length=200,
        help_text=(
            "Briefly describe the primary cause of the incident, for example "
            "'inadequate equipment', 'inexperience', 'poor judgement', etc."
        ),
        blank=True,
    )
    secondary_cause = models.CharField(
        max_length=200,
        blank=True,
        help_text="Briefly describe the secondary cause of the incident.",
    )
    group_type = models.CharField(
        max_length=2,
        choices=GroupType.choices,
        default=GroupType.UNKNOWN,
        help_text="The type of group involved in the incident.",
    )
    group_size = models.IntegerField(
        blank=True,
        null=True,
        help_text=(
            "The number of people involved in the incident, excluding "
            "any rescue or aid teams."
        ),
    )
    aid_type = models.CharField(
        max_length=2,
        choices=AidType.choices,
        default=AidType.UNKNOWN,
        help_text="The type of aid required.",
    )
    fatality = models.BooleanField(
        default=False,
        help_text="Tick this box if somebody died as a result of this incident.",
    )

    injury = models.BooleanField(
        default=False,
        help_text="Tick this box if somebody was injured as a result of this incident.",
    )
    multiple_incidents = models.BooleanField(
        default=False,
        help_text=(
            "Tick this box if there were multiple incidents, e.g. several falls."
        ),
    )
    rescue_over_24_hours = models.BooleanField(
        default=False,
        verbose_name="Rescue duration over 24 hours",
        help_text="Tick this box if the rescue took over 24 hours.",
    )
    vertical = models.BooleanField(
        default=False,
        verbose_name="Vertical incident",
        help_text="Tick this box if the incident involved vertical caving.",
    )
    spar = models.BooleanField(
        default=False,
        verbose_name="SPAR",
        help_text="Tick this box if SPAR (self-rescue) techniques were used.",
    )
    source = models.CharField(
        max_length=2,
        choices=Source.choices,
        default=Source.UNKNOWN,
        help_text="The source of the incident information.",
    )
    original_text = models.TextField(
        blank=True,
        help_text=(
            "The original text of the incident report from the "
            "publication, before any human or AI processing."
        ),
    )
    incident_report = models.TextField(
        blank=True,
        help_text=(
            "The text of the incident report from the publication. Any references to "
            "external publications, such as websites, journals or books, should "
            "be removed and placed into the references field below. Any analysis "
            "of the incident should be placed into the analysis field below."
        ),
    )
    incident_analysis = models.TextField(blank=True)
    incident_references = models.TextField(verbose_name="references", blank=True)
    incident_notes = models.TextField(
        verbose_name="notes",
        blank=True,
        help_text=(
            "Any additional notes about the incident, as you see fit. This could "
            "include information about the incident that is not included in the "
            "original text, or any other information that you feel is relevant."
        ),
    )
    incident_summary = models.TextField(
        verbose_name="summary",
        blank=True,
        max_length=400,
        help_text="A short summary of the incident. Maximum 400 characters.",
    )

    # Meta fields related to the editing of the incident record
    editing_notes = models.TextField(
        blank=True,
        help_text=(
            "Notes that will be visible only to people editing this "
            "incident on this website. For example: 'need to find the "
            "exact date of this incident'. Adding editing notes to an "
            "incident will force it to be reviewed and prevent approval. "
            "These notes will not be visible to the public."
        ),
    )
    approved = models.BooleanField(
        default=False,
        help_text=(
            "Tick this box if you have reviewed the data for this incident and "
            "are satisfied that it is correct and ready for publication."
        ),
    )
    data_input_source = models.CharField(
        max_length=2,
        choices=DataInput.choices,
        default=DataInput.HUMAN,
        help_text=(
            "The source of the data for this incident. If the data was entered "
            "by a human, select 'Human'. If the data was generated by an AI, "
            "select 'AI'."
        ),
    )
    no_analysis = models.BooleanField(
        default=False,
        help_text="Tick this box if the original report contained no analysis.",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    objects = IncidentManager()

    def __str__(self):
        return self.date.strftime("%Y-%m-%d") + " " + self.cave

    def get_absolute_url(self):
        return reverse("db:incident_detail", kwargs={"pk": self.pk})

    def empty_fields(self):
        """Return a list of fields that are empty."""
        exclude_fields = [
            "id",
            "created",
            "updated",
            "updated_by",
            "editing_notes",
            "incident_notes",
            "keywords",
            "original_text",
        ]
        empty_fields = []
        for field in self._meta.fields:
            if field.name not in exclude_fields:
                if getattr(self, field.name) is None or getattr(self, field.name) == "":
                    empty_fields.append(field.verbose_name)
                if getattr(self, field.name) == "YY":  # code for unknown in choices
                    empty_fields.append(field.verbose_name)

        return empty_fields


@reversion.register()
class InjuredCaver(models.Model):
    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE, related_name="injured_cavers"
    )
    first_name = models.CharField(
        max_length=100,
        help_text="The first name of the injured caver.",
        blank=True,
    )
    surname = models.CharField(
        max_length=100,
        help_text="The surname of the injured caver.",
        blank=True,
    )
    age = models.IntegerField(
        blank=True,
        null=True,
        help_text="The age of the injured caver at the time of the incident.",
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    sex = models.CharField(
        max_length=10,
        blank=True,
        choices=(("", "Not recorded"), ("Male", "Male"), ("Female", "Female")),
        help_text="The sex of the injured caver.",
    )
    injuries = models.CharField(
        max_length=200,
        blank=True,
        help_text="The injuries sustained by the injured caver.",
    )
    injury_areas = models.CharField(
        max_length=200,
        blank=True,
        help_text="The areas of the body that were injured.",
    )

    def __str__(self):
        return " ".join([self.first_name, self.surname]) + " in " + self.incident.cave

    def get_absolute_url(self):
        return reverse("db:incident_detail", kwargs={"pk": self.incident.pk})

    def get_update_form(self):
        from .forms import InjuredCaverForm

        return InjuredCaverForm(instance=self, incident=self.incident)
