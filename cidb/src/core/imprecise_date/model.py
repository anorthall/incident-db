import datetime
import re
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Literal, Self, assert_never

_SEPARATOR = r"[-./]"
_MONTH = r"0[1-9]|1[0-2]"
_DAY = r"0[1-9]|[12]\d|3[01]"
_SEASON = r"spring|summer|autumn|fall|winter"

_IMPRECISE_DATE_PATTERN = (
    rf"^(?P<year>\d{{4}})"
    rf"(?:{_SEPARATOR}(?:(?P<month>{_MONTH})|(?P<season>{_SEASON})))?"
    rf"(?:{_SEPARATOR}(?P<day>{_DAY}))?$"
)

_IMPRECISE_DATE_REGEX = re.compile(_IMPRECISE_DATE_PATTERN, re.IGNORECASE)


class DatePrecision(Enum):
    YEAR = 1
    SEASON = 2
    MONTH = 3
    DAY = 4


class Season(StrEnum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


_SEASON_MONTH_MAP = {
    Season.WINTER: [12, 1, 2],
    Season.SPRING: [3, 4, 5],
    Season.SUMMER: [6, 7, 8],
    Season.AUTUMN: [9, 10, 11],
}


@dataclass(frozen=True)
class ImpreciseDate:
    _raw: str
    _parsed: tuple[datetime.date, DatePrecision] | None = field(default=None, init=False)
    _season: Season | None | Literal["UNSET"] = field(default="UNSET", init=False)

    @classmethod
    def from_date(cls, year: int, month: int | None = None, day: int | None = None) -> Self:
        if not isinstance(year, int) or year < 1:
            raise ValueError("Year must be a positive integer.")

        year_str = f"{year:04d}"

        if month is None:
            if day is not None:
                raise ValueError("Day must be None if month is None.")
            return cls(year_str)

        if not (1 <= month <= 12):
            raise ValueError(f"Month must be between 1 and 12, got '{month}'")

        month_str = f"{month:02d}"

        if day is None:
            return cls(f"{year_str}-{month_str}")

        try:
            datetime.date(year, month, day)
        except ValueError as e:
            raise ValueError(f"Invalid date: {e}") from e

        if not (1 <= day <= 31):
            raise ValueError(f"Day must be between 1 and 31, got '{day}'")

        return cls(f"{year_str}-{month_str}-{day:02d}")

    @classmethod
    def from_season(cls, year: int, season: Season) -> Self:
        if not isinstance(year, int) or year < 1:
            raise ValueError("Year must be a positive integer.")

        return cls(f"{year:04d}-{season}")

    def __post_init__(self) -> None:
        if not _IMPRECISE_DATE_REGEX.match(self._raw):
            raise ValueError(f"Invalid imprecise date format: {self._raw}")

        # object.__setattr__ as frozen dataclass workaround
        object.__setattr__(self, "_parsed", self._parse())

    def __str__(self) -> str:
        date, precision = self._parse()
        match precision:
            case DatePrecision.YEAR:
                return date.strftime("%Y")
            case DatePrecision.MONTH:
                return date.strftime("%B %Y")
            case DatePrecision.SEASON:
                season = self.season
                if not season:
                    raise ValueError("Season must be set for seasonal precision.")
                return f"{season.title()} {date.year}"
            case DatePrecision.DAY:
                return date.strftime("%B %d, %Y")
            case _:
                assert_never(precision)

    def __repr__(self) -> str:
        return f"ImpreciseDate(raw='{self._raw}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ImpreciseDate):
            return NotImplemented
        return self.date == other.date and self.precision == other.precision

    def __gt__(self, other: ImpreciseDate) -> bool:
        if not isinstance(other, ImpreciseDate):
            return NotImplemented
        return self.date > other.date

    def _parse(self) -> tuple[datetime.date, DatePrecision]:
        if self._parsed is not None:
            return self._parsed

        match = _IMPRECISE_DATE_REGEX.match(self._raw)
        if not match:
            raise ValueError(f"Invalid imprecise date format: {self._raw}")

        year = int(match.group("year"))
        if year < 1:
            raise ValueError(f"Year must be a positive integer, got '{year}'")

        month_str = match.group("month")
        day_str = match.group("day")
        season_str = match.group("season")

        # Year only
        if month_str is None and season_str is None:
            return datetime.date(year, 1, 1), DatePrecision.YEAR

        # Season (normalize "fall" to "autumn")
        if season_str is not None:
            if day_str is not None:
                raise ValueError("Cannot specify day with season precision")
            season_normalized = "autumn" if season_str.lower() == "fall" else season_str.lower()
            season = Season(season_normalized)
            month = _SEASON_MONTH_MAP[season][0]
            return datetime.date(year, month, 1), DatePrecision.SEASON

        # Month (with optional day)
        month = int(month_str)
        if not (1 <= month <= 12):
            raise ValueError(f"Month must be between 1 and 12, got '{month}'")

        if day_str is None:
            return datetime.date(year, month, 1), DatePrecision.MONTH

        day = int(day_str)
        if not (1 <= day <= 31):
            raise ValueError(f"Day must be between 1 and 31, got '{day}'")

        return datetime.date(year, month, day), DatePrecision.DAY

    @property
    def date(self) -> datetime.date:
        return self._parse()[0]

    @property
    def precision(self) -> DatePrecision:
        return self._parse()[1]

    @property
    def season(self) -> Season | None:
        if isinstance(self._season, Season) or self._season is None:
            return self._season

        date, precision = self._parse()
        if precision not in [DatePrecision.SEASON, DatePrecision.MONTH, DatePrecision.DAY]:
            object.__setattr__(self, "_season", None)
            return None

        for season, months in _SEASON_MONTH_MAP.items():
            if date.month in months:
                object.__setattr__(self, "_season", season)
                return season

        raise RuntimeError("Month must be between 1 and 12")

    @property
    def year(self) -> int:
        return self.date.year

    @property
    def month(self) -> int | None:
        if self.precision in [DatePrecision.MONTH, DatePrecision.DAY]:
            return self.date.month
        return None

    @property
    def day(self) -> int | None:
        if self.precision == DatePrecision.DAY:
            return self.date.day
        return None
