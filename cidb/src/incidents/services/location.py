from django.db import transaction

from cidb.src.incidents.models.location import GeographicArea, GeographicAreaKind


def create_country(name: str, code: str = "") -> GeographicArea:
    return GeographicArea.add_root(name=name, kind=GeographicAreaKind.COUNTRY, code=code)


def create_state(name: str, parent: GeographicArea, code: str = "") -> GeographicArea:
    if parent.get_kind() != GeographicAreaKind.COUNTRY:
        raise ValueError("States must be added to a country")

    parent.refresh_from_db()
    return parent.add_child(name=name, kind=GeographicAreaKind.STATE, code=code)


def create_region(name: str, parent: GeographicArea) -> GeographicArea:
    if parent.get_kind() not in (GeographicAreaKind.COUNTRY, GeographicAreaKind.STATE):
        raise ValueError("Regions must be added to a country or state")

    parent.refresh_from_db()
    return parent.add_child(name=name, kind=GeographicAreaKind.REGION, code="")


def get_or_create_country(
    name: str,
    code: str = "",
) -> tuple[GeographicArea, bool]:
    with transaction.atomic():
        area = GeographicArea.objects.filter(
            kind=GeographicAreaKind.COUNTRY,
            code=code,
        ).first()

        if area is not None:
            return area, False

        return create_country(name, code), True


def get_or_create_state(
    name: str,
    parent: GeographicArea,
    code: str = "",
) -> tuple[GeographicArea, bool]:
    with transaction.atomic():
        area = GeographicArea.objects.filter(
            kind=GeographicAreaKind.STATE,
            code=code,
            path__startswith=parent.path,
            depth=parent.depth + 1,
        ).first()

        if area is not None:
            return area, False

        return create_state(name, parent, code), True


def get_or_create_region(
    name: str,
    parent: GeographicArea,
) -> tuple[GeographicArea, bool]:
    with transaction.atomic():
        area = GeographicArea.objects.filter(
            kind=GeographicAreaKind.REGION,
            name=name,
            path__startswith=parent.path,
            depth=parent.depth + 1,
        ).first()

        if area is not None:
            return area, False

        return create_region(name, parent), True
