from uuid import uuid7

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta


class UUIDPKModel(models.Model):
    id = models.UUIDField(
        unique=True,
        default=uuid7,
        editable=False,
        primary_key=True,
    )

    class Meta(TypedModelMeta):
        abstract = True


class TimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(TypedModelMeta):
        abstract = True
