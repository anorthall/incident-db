from ninja import Schema

from cidb.src.core.imprecise_date import ImpreciseDate


class ImpreciseDateSchema(Schema):
    raw: str
    display: str
    year: int
    month: int | None = None
    day: int | None = None
    season: str | None = None
    precision: str

    @classmethod
    def from_imprecise_date(cls, date: ImpreciseDate | None) -> ImpreciseDateSchema | None:
        if date is None:
            return None
        return cls(
            raw=date._raw,
            display=str(date),
            year=date.year,
            month=date.month,
            day=date.day,
            season=date.season.value if date.season else None,
            precision=date.precision.name.lower(),
        )


class PaginatedResponse[T](Schema):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
