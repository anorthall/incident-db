from django.contrib.postgres.fields import ArrayField
from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from cidb.src.core.models.generic import TimestampModel


class DuplicateStatus(models.TextChoices):
    PENDING = "pending", "Pending Review"
    CONFIRMED = "confirmed", "Confirmed Duplicate"
    REJECTED = "rejected", "Not a Duplicate"
    MERGED = "merged", "Merged"


class DuplicateGroup(TimestampModel):
    status = models.CharField(
        choices=DuplicateStatus.choices,
        default=DuplicateStatus.PENDING,
    )
    primary_incident = models.ForeignKey(
        "Incident",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="primary_of_groups",
    )
    notes = models.TextField(
        blank=True,
    )

    def __str__(self) -> str:
        return f"DuplicateGroup {self.id}"


class DuplicateGroupMember(TimestampModel):
    group = models.ForeignKey(
        DuplicateGroup,
        on_delete=models.CASCADE,
        related_name="members",
    )
    incident = models.ForeignKey(
        "Incident",
        on_delete=models.CASCADE,
        related_name="duplicate_memberships",
    )
    similarity_score = models.FloatField()
    llm_confidence = models.IntegerField(
        null=True,
        blank=True,
    )
    llm_reasoning = models.TextField(
        blank=True,
    )

    class Meta(TypedModelMeta):
        constraints = [
            models.UniqueConstraint(
                fields=["group", "incident"],
                name="incidents_duplicategroupmember_unique_group_incident",
            ),
        ]

    def __str__(self) -> str:
        return f"Member: {self.incident} in Group {self.group_id}"


class IncidentEmbedding(TimestampModel):
    incident = models.OneToOneField(
        "Incident",
        on_delete=models.CASCADE,
        related_name="embedding",
    )
    embedding = ArrayField(
        models.FloatField(),
        size=1536,
    )
    model_version = models.CharField(
        max_length=50,
        default="text-embedding-3-small",
    )

    def __str__(self) -> str:
        return f"Embedding for Incident {self.incident_id}"
