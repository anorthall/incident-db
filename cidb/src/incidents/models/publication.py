from __future__ import annotations

from functools import partial

from django.db import models
from django.db.models import Q
from django_stubs_ext.db.models import TypedModelMeta

from cidb.src.core.imprecise_date import ImpreciseDateField
from cidb.src.core.models.generic import TimestampModel, UUIDPKModel


def _asset_upload_path(instance: Document, filename: str, filetype: str) -> str:
    return f"doc/{str(instance.pk)}/{filename}.{filetype}"


class Document(TimestampModel, UUIDPKModel):
    text = models.TextField(
        blank=True,
    )
    image = models.ImageField(
        upload_to=partial(_asset_upload_path, filetype="jpg"),
        blank=True,
    )
    pdf = models.FileField(
        upload_to=partial(_asset_upload_path, filetype="pdf"),
        blank=True,
    )

    class Meta(TypedModelMeta):
        constraints = [
            models.CheckConstraint(
                condition=~Q(text="") | ~Q(image="") | ~Q(pdf=""),
                name="publication_document_at_least_one_asset",
            ),
        ]


class AuthorKind(models.TextChoices):
    INDIVIDUAL = "individual", "Individual"
    ORGANIZATION = "organization", "Organization"


class Author(TimestampModel):
    name = models.CharField()
    kind = models.CharField(choices=AuthorKind.choices)

    def __str__(self) -> str:
        return self.name


class PublicationPage(TimestampModel):
    number = models.PositiveIntegerField()
    publication = models.ForeignKey(
        "Publication",
        related_name="pages",
        on_delete=models.CASCADE,
    )
    document = models.OneToOneField(
        Document,
        on_delete=models.PROTECT,
        related_name="publication_page",
    )

    class Meta(TypedModelMeta):
        constraints = [
            models.UniqueConstraint(
                fields=["number", "publication"],
                name="publication_page_unique_number_per_publication",
            ),
        ]

    def __str__(self) -> str:
        return f"Page {self.number}"


class Publication(TimestampModel):
    title = models.CharField(
        max_length=255,
    )
    authors = models.ManyToManyField(
        Author,
        related_name="publications",
    )
    content = models.OneToOneField(
        Document,
        on_delete=models.PROTECT,
        related_name="publication",
    )
    website = models.URLField(
        blank=True,
        max_length=255,
    )
    published_at = ImpreciseDateField()

    def __str__(self) -> str:
        return self.title
