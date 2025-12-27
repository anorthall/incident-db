from django.db import models

from cidb.src.core.models.generic import TimestampModel


class Tag(TimestampModel):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name
