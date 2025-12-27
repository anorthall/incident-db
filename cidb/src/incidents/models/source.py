from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from cidb.src.core.models.generic import TimestampModel, UUIDPKModel
from cidb.src.incidents.models.publication import Document, Publication


class SourceFile(TimestampModel, UUIDPKModel):
    filename = models.CharField()
    document = models.OneToOneField(
        Document,
        on_delete=models.PROTECT,
        related_name="source_file",
    )
    publication = models.ForeignKey(
        Publication,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="source_files",
    )

    def __str__(self) -> str:
        return self.filename


class SourceExtract(TimestampModel):
    source_file = models.ForeignKey(
        SourceFile,
        on_delete=models.CASCADE,
        related_name="extracts",
    )
    sequence = models.PositiveIntegerField()
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta(TypedModelMeta):
        constraints = [
            models.UniqueConstraint(
                fields=["source_file", "sequence"],
                name="incidents_sourceextract_unique_source_sequence",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.source_file.filename} [{self.sequence}]"
