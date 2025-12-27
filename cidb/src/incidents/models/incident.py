from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from cidb.src.core.imprecise_date import ImpreciseDateField
from cidb.src.core.models.generic import TimestampModel
from cidb.src.incidents.models.cave import Cave
from cidb.src.incidents.models.person import Person
from cidb.src.incidents.models.publication import Publication
from cidb.src.incidents.models.tag import Tag


class Injury(TimestampModel):
    description = models.CharField(
        max_length=200,
        unique=True,
    )

    def __str__(self) -> str:
        return self.description


class IncidentReference(TimestampModel):
    incident = models.ForeignKey(
        "Incident",
        on_delete=models.CASCADE,
        related_name="references",
    )
    index = models.PositiveSmallIntegerField(default=0)
    author = models.CharField(blank=True)
    title = models.CharField(blank=True)
    source = models.CharField(blank=True)
    reference_date = ImpreciseDateField()
    raw_citation = models.TextField(blank=True)

    class Meta(TypedModelMeta):
        constraints = [
            models.UniqueConstraint(
                fields=["incident", "index"],
                name="incidents_incidentreference_unique_index",
            ),
        ]


class IncidentPerson(TimestampModel):
    incident = models.ForeignKey(
        "Incident",
        on_delete=models.CASCADE,
        related_name="persons_involved",
    )
    person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="incident_involvements",
    )
    age_at_incident = models.PositiveSmallIntegerField(null=True, blank=True)
    injuries = models.ManyToManyField(
        Injury,
        blank=True,
        related_name="persons_injured",
    )

    class Meta(TypedModelMeta):
        constraints = [
            models.UniqueConstraint(
                fields=["incident", "person"],
                name="incidents_incidentperson_unique_incident_person",
            ),
        ]


class Incident(TimestampModel):
    origin = models.ForeignKey(
        Publication,
        on_delete=models.PROTECT,
        related_name="published_incidents",
    )
    source_extract = models.OneToOneField(
        "SourceExtract",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="incident",
    )

    title = models.CharField(
        max_length=100,
    )

    cave = models.ForeignKey(
        Cave,
        on_delete=models.PROTECT,
        related_name="incidents",
    )

    date = ImpreciseDateField()
    time = models.TimeField(
        blank=True,
        null=True,
    )

    report = models.TextField(
        blank=True,
    )
    analysis = models.TextField(
        blank=True,
    )
    summary = models.TextField(
        blank=True,
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="incidents",
    )

    view_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this incident has been viewed",
    )

    search_vector = SearchVectorField(null=True, blank=True)

    class Meta(TypedModelMeta):
        indexes = [
            GinIndex(fields=["search_vector"]),
            models.Index(fields=["view_count"], name="incidents_incident_view_count"),
            models.Index(fields=["origin"], name="incidents_incident_origin"),
            models.Index(fields=["date"], name="incidents_incident_date"),
        ]

    def __str__(self) -> str:
        return self.title

    @classmethod
    def increment_view_count(cls, incident_id: int) -> int:
        from django.db.models import F

        return cls.objects.filter(pk=incident_id).update(view_count=F("view_count") + 1)
