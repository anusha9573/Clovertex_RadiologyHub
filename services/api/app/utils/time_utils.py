from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional, Union


def parse_iso_date(value: Union[str, date]) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def parse_iso_time(value: Union[str, time]) -> time:
    if isinstance(value, time):
        return value
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(str(value), fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Unsupported time format: {value}")


def combine_date_time(d: Union[str, date], t: Union[str, time]) -> datetime:
    return datetime.combine(parse_iso_date(d), parse_iso_time(t))


def is_within_window(
    start_str: str, end_str: str, target: Union[str, time]
) -> bool:
    target_time = parse_iso_time(target)
    start_time = parse_iso_time(start_str)
    end_time = parse_iso_time(end_str)
    return start_time <= target_time <= end_time
