import datetime

import pytest

from cidb.src.core.imprecise_date.field import ImpreciseDateField
from cidb.src.core.imprecise_date.model import DatePrecision, ImpreciseDate, Season


def test_from_date_year_only() -> None:
    date = ImpreciseDate.from_date(2024)
    assert date._raw == "2024"
    assert date.date == datetime.date(2024, 1, 1)
    assert date.precision == DatePrecision.YEAR
    assert str(date) == "2024"


def test_from_date_year_and_month() -> None:
    date = ImpreciseDate.from_date(2024, 6)
    assert date._raw == "2024-06"
    assert date.date == datetime.date(2024, 6, 1)
    assert date.precision == DatePrecision.MONTH
    assert str(date) == "June 2024"


def test_from_date_full_date() -> None:
    date = ImpreciseDate.from_date(2024, 6, 15)
    assert date._raw == "2024-06-15"
    assert date.date == datetime.date(2024, 6, 15)
    assert date.precision == DatePrecision.DAY
    assert str(date) == "June 15, 2024"


def test_from_date_invalid_year_zero() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        ImpreciseDate.from_date(0)


def test_from_date_invalid_year_negative() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        ImpreciseDate.from_date(-1)


def test_from_date_invalid_year_not_int() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        ImpreciseDate.from_date("2024")  # type: ignore[arg-type]


def test_from_date_invalid_month_zero() -> None:
    with pytest.raises(ValueError, match="Month must be between 1 and 12"):
        ImpreciseDate.from_date(2024, 0)


def test_from_date_invalid_month_13() -> None:
    with pytest.raises(ValueError, match="Month must be between 1 and 12"):
        ImpreciseDate.from_date(2024, 13)


def test_from_date_invalid_day_with_none_month() -> None:
    with pytest.raises(ValueError, match="Day must be None if month is None"):
        ImpreciseDate.from_date(2024, None, 15)


def test_from_date_invalid_date_feb_30() -> None:
    with pytest.raises(ValueError, match="Invalid date"):
        ImpreciseDate.from_date(2024, 2, 30)


def test_from_season_spring() -> None:
    date = ImpreciseDate.from_season(2024, Season.SPRING)
    assert date._raw == "2024-spring"
    assert date.date == datetime.date(2024, 3, 1)
    assert date.precision == DatePrecision.SEASON
    assert date.season == Season.SPRING
    assert str(date) == "Spring 2024"


def test_from_season_summer() -> None:
    date = ImpreciseDate.from_season(2024, Season.SUMMER)
    assert date._raw == "2024-summer"
    assert date.date == datetime.date(2024, 6, 1)
    assert date.precision == DatePrecision.SEASON
    assert date.season == Season.SUMMER
    assert str(date) == "Summer 2024"


def test_from_season_autumn() -> None:
    date = ImpreciseDate.from_season(2024, Season.AUTUMN)
    assert date._raw == "2024-autumn"
    assert date.date == datetime.date(2024, 9, 1)
    assert date.precision == DatePrecision.SEASON
    assert date.season == Season.AUTUMN
    assert str(date) == "Autumn 2024"


def test_from_season_winter() -> None:
    date = ImpreciseDate.from_season(2024, Season.WINTER)
    assert date._raw == "2024-winter"
    assert date.date == datetime.date(2024, 12, 1)
    assert date.precision == DatePrecision.SEASON
    assert date.season == Season.WINTER
    assert str(date) == "Winter 2024"


def test_from_season_invalid_year() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        ImpreciseDate.from_season(0, Season.SUMMER)


@pytest.mark.parametrize("separator", ["-", ".", "/"])
def test_parse_separators_month(separator: str) -> None:
    date = ImpreciseDate(f"2024{separator}06")
    assert date.date == datetime.date(2024, 6, 1)
    assert date.precision == DatePrecision.MONTH


@pytest.mark.parametrize("separator", ["-", ".", "/"])
def test_parse_separators_day(separator: str) -> None:
    date = ImpreciseDate(f"2024{separator}06{separator}15")
    assert date.date == datetime.date(2024, 6, 15)
    assert date.precision == DatePrecision.DAY


@pytest.mark.parametrize("separator", ["-", ".", "/"])
def test_parse_separators_season(separator: str) -> None:
    date = ImpreciseDate(f"2024{separator}summer")
    assert date.date == datetime.date(2024, 6, 1)
    assert date.precision == DatePrecision.SEASON


def test_parse_fall_normalized_to_autumn() -> None:
    date = ImpreciseDate("2024-fall")
    assert date.season == Season.AUTUMN
    assert str(date) == "Autumn 2024"


def test_parse_case_insensitive_season() -> None:
    date = ImpreciseDate("2024-SUMMER")
    assert date.season == Season.SUMMER


def test_parse_case_insensitive_fall() -> None:
    date = ImpreciseDate("2024-FALL")
    assert date.season == Season.AUTUMN


def test_parse_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid imprecise date format"):
        ImpreciseDate("not-a-date")


def test_parse_invalid_format_empty() -> None:
    with pytest.raises(ValueError, match="Invalid imprecise date format"):
        ImpreciseDate("")


@pytest.mark.parametrize(
    "month,expected_season",
    [
        (1, Season.WINTER),
        (2, Season.WINTER),
        (3, Season.SPRING),
        (4, Season.SPRING),
        (5, Season.SPRING),
        (6, Season.SUMMER),
        (7, Season.SUMMER),
        (8, Season.SUMMER),
        (9, Season.AUTUMN),
        (10, Season.AUTUMN),
        (11, Season.AUTUMN),
        (12, Season.WINTER),
    ],
)
def test_season_from_month(month: int, expected_season: Season) -> None:
    date = ImpreciseDate.from_date(2024, month)
    assert date.season == expected_season


def test_season_none_for_year_only() -> None:
    date = ImpreciseDate.from_date(2024)
    assert date.season is None


def test_field_from_db_value_none() -> None:
    field = ImpreciseDateField()
    assert field.from_db_value(None, None, None) is None


def test_field_from_db_value_empty() -> None:
    field = ImpreciseDateField()
    assert field.from_db_value("", None, None) is None


def test_field_from_db_value_valid() -> None:
    field = ImpreciseDateField()
    result = field.from_db_value("2024-06-15", None, None)
    assert isinstance(result, ImpreciseDate)
    assert result.date == datetime.date(2024, 6, 15)


def test_field_to_python_none() -> None:
    field = ImpreciseDateField()
    assert field.to_python(None) is None


def test_field_to_python_empty() -> None:
    field = ImpreciseDateField()
    assert field.to_python("") is None


def test_field_to_python_string() -> None:
    field = ImpreciseDateField()
    result = field.to_python("2024-06")
    assert isinstance(result, ImpreciseDate)
    assert result.precision == DatePrecision.MONTH


def test_field_to_python_imprecise_date() -> None:
    field = ImpreciseDateField()
    original = ImpreciseDate.from_date(2024, 6)
    result = field.to_python(original)
    assert result is original


def test_field_get_prep_value_none() -> None:
    field = ImpreciseDateField()
    assert field.get_prep_value(None) is None


def test_field_get_prep_value_imprecise_date() -> None:
    field = ImpreciseDateField()
    date = ImpreciseDate.from_date(2024, 6, 15)
    assert field.get_prep_value(date) == "2024-06-15"


def test_field_get_prep_value_string() -> None:
    field = ImpreciseDateField()
    assert field.get_prep_value("2024-06") == "2024-06"
