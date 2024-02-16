from __future__ import annotations

import datetime
import typing as t

from .base import FieldFormatter


class StrFormatter(FieldFormatter[str]):
    def parse(self, value: t.Any) -> str:
        return str(value)

    def render(self, value: str) -> str:
        return value


class DateFormatter(FieldFormatter[t.Union[datetime.datetime, datetime.date]]):
    def parse(self, value: t.Any) -> datetime.datetime | datetime.date:
        if not isinstance(value, str):
            raise ValueError("cannot parse date from non-str value")
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            return datetime.datetime.fromisoformat(value)

    def render(self, value: datetime.datetime | datetime.date) -> str:
        if isinstance(value, datetime.datetime):
            if value.tzinfo is None:
                return value.strftime("%Y-%m-%d %H:%M:%S")
            return value.astimezone().strftime("%Y-%m-%d %H:%M:%S")

        return value.strftime("%Y-%m-%d")


class BoolFormatter(FieldFormatter[bool]):
    def __init__(self, *, true_str: str = "True", false_str: str = "False") -> None:
        self.true_str = true_str
        self.false_str = false_str

    def parse(self, value: t.Any) -> bool:
        if not isinstance(value, bool):
            raise ValueError("bad bool value")
        return value

    def render(self, value: bool) -> str:
        if value:
            return self.true_str
        return self.false_str


class FuzzyBoolFormatter(BoolFormatter):
    parse_null_values = True

    def parse(self, value: t.Any) -> bool:
        return bool(value)


class StaticStringFormatter(StrFormatter):
    def __init__(self, value: str) -> None:
        self.value = value

    def parse(self, value: t.Any) -> str:
        return self.value
