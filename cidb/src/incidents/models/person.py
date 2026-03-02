from django.db import models
from django.db.models import TextChoices

from cidb.src.core.models.generic import TimestampModel
from cidb.src.incidents.models.location import GeographicArea


class Gender(TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    NON_BINARY = "non-binary", "Non-binary"
    GENDERFLUID = "genderfluid", "Genderfluid"
    AGENDER = "agender", "Agender"


class Person(TimestampModel):
    name = models.CharField(
        max_length=255,
        db_index=True,
    )
    location = models.ForeignKey(
        GeographicArea,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )
    gender = models.CharField(
        blank=True,
        default="",
        choices=Gender.choices,
    )

    def __str__(self) -> str:
        return self.name
