from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django_stubs_ext.db.models import TypedModelMeta
from treebeard.mp_tree import MP_Node

from cidb.src.core.models.generic import TimestampModel


class GeographicAreaKind(models.TextChoices):
    COUNTRY = "country", "Country"
    STATE = "state", "State"
    REGION = "region", "Region"


_VALID_GEOGRAPHIC_AREA_PARENTS: dict[GeographicAreaKind, list[GeographicAreaKind] | None] = {
    GeographicAreaKind.COUNTRY: None,
    GeographicAreaKind.STATE: [GeographicAreaKind.COUNTRY],
    GeographicAreaKind.REGION: [GeographicAreaKind.COUNTRY, GeographicAreaKind.STATE],
}


class GeographicArea(MP_Node, TimestampModel):
    name = models.CharField(
        max_length=100,
    )

    kind = models.CharField(
        max_length=20,
        choices=GeographicAreaKind.choices,
    )

    code = models.CharField(
        max_length=10,
        blank=True,
    )

    node_order_by = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_kind(self) -> GeographicAreaKind:
        return GeographicAreaKind(self.kind)

    def clean(self) -> None:
        super().clean()
        parent = self.get_parent()

        allowed = _VALID_GEOGRAPHIC_AREA_PARENTS.get(self.get_kind())

        if allowed is None:
            if parent:
                raise ValidationError("Countries cannot have a parent.")

        else:
            if not parent:
                raise ValidationError(f"{self.get_kind()} requires a parent.")

            if parent.get_kind() not in allowed:
                raise ValidationError(
                    f"{self.get_kind()} must be under a {' or '.join(allowed)}, "
                    f"not a {parent.get_kind()}."
                )

    def get_country(self) -> GeographicArea:
        if self.get_kind() == GeographicAreaKind.COUNTRY:
            return self

        country = self.get_ancestors().filter(kind=GeographicAreaKind.COUNTRY).first()

        if country is None:
            raise ValueError(f"GeographicArea #{self.pk} has no country ancestor")

        return country

    def get_state(self) -> GeographicArea | None:
        if self.get_kind() == GeographicAreaKind.STATE:
            return self

        if self.get_kind() == GeographicAreaKind.COUNTRY:
            return None

        return self.get_ancestors().filter(kind=GeographicAreaKind.STATE).first()


class Location(TimestampModel):
    country_text = models.CharField(max_length=100)
    state_text = models.CharField(max_length=100, blank=True)
    region_text = models.CharField(max_length=100, blank=True)

    canonical_area = models.ForeignKey(
        GeographicArea,
        null=True,
        blank=True,
        related_name="locations",
        on_delete=models.PROTECT,
    )

    latitude = models.DecimalField(
        null=True,
        blank=True,
        max_digits=8,
        decimal_places=5,
    )
    longitude = models.DecimalField(
        null=True,
        blank=True,
        max_digits=8,
        decimal_places=5,
    )

    class Meta(TypedModelMeta):
        indexes = [
            models.Index(fields=["country_text"], name="incidents_location_country"),
            models.Index(fields=["state_text"], name="incidents_location_state"),
            models.Index(fields=["region_text"], name="incidents_location_region"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(latitude__gte=-90, latitude__lte=90) | Q(latitude__isnull=True),
                name="incidents_location_valid_latitude",
            ),
            models.CheckConstraint(
                condition=Q(longitude__gte=-180, longitude__lte=180) | Q(longitude__isnull=True),
                name="incidents_location_valid_longitude",
            ),
        ]

    def __str__(self) -> str:
        parts = [p for p in [self.region_text, self.state_text, self.country_text] if p]
        return ", ".join(parts) or "Unknown Location"
