from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from django.db import models
from django.db.models import Model

from cidb.src.core.imprecise_date.model import ImpreciseDate

_MAX_LENGTH = 11

type _ImpreciseDateValueType = str | ImpreciseDate | None


class ImpreciseDateField(models.CharField[_ImpreciseDateValueType, ImpreciseDate]):
    """A Django model field for storing dates with variable precision."""

    description = "A date with variable precision (year, season, month, or day)"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("max_length", _MAX_LENGTH)
        super().__init__(*args, **kwargs)

    def from_db_value(self, value: str | None, _expr: Any, _conn: Any) -> ImpreciseDate | None:
        if value is None or value == "":
            return None
        return ImpreciseDate(value)

    def to_python(self, value: _ImpreciseDateValueType) -> ImpreciseDate | None:
        if value is None or value == "":
            return None
        if isinstance(value, ImpreciseDate):
            return value
        return ImpreciseDate(value)

    def get_prep_value(self, value: _ImpreciseDateValueType) -> str | None:
        if value is None:
            return None
        if isinstance(value, ImpreciseDate):
            return value._raw
        return value

    def value_to_string(self, obj: Model) -> str:
        return self.get_prep_value(self.value_from_object(obj)) or ""

    def deconstruct(self) -> tuple[str, str, Sequence[Any], dict[Any, Any]]:
        name, path, args, kwargs = super().deconstruct()
        kwargs["max_length"] = _MAX_LENGTH
        return name, path, args, kwargs
