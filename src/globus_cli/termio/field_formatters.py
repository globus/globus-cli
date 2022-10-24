from __future__ import annotations

import abc
import datetime
import json
import typing as t
import warnings

T = t.TypeVar("T")
JSON = t.Union[dict, list, str, int, float, bool, None]


class FormattingFailedWarning(UserWarning):
    pass


class FieldFormatter(abc.ABC, t.Generic[T]):
    parse_null_values: bool = False

    def warn_formatting_failed(self, value: t.Any) -> None:
        warnings.warn(
            f"Formatting failed for '{value!r}' with formatter={self!r}",
            FormattingFailedWarning,
        )

    @abc.abstractmethod
    def parse(self, value: t.Any) -> T:
        ...

    @abc.abstractmethod
    def render(self, value: T) -> str:
        ...

    def format(self, value: t.Any) -> str:
        if value is None and self.parse_null_values is False:
            return "None"
        try:
            data = self.parse(value)
            return self.render(data)
        except ValueError:
            self.warn_formatting_failed(value)
            return str(value)


class StrFieldFormatter(FieldFormatter[str]):
    def parse(self, value: t.Any) -> str:
        return str(value)

    def render(self, value: str) -> str:
        return value


class DateFieldFormatter(FieldFormatter[datetime.datetime]):
    def parse(self, value: t.Any) -> datetime.datetime:
        return datetime.datetime.fromisoformat(value)

    def render(self, value: datetime.datetime) -> str:
        if value.tzinfo is None:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return value.astimezone().strftime("%Y-%m-%d %H:%M:%S")


class BoolFieldFormatter(FieldFormatter[bool]):
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


class FuzzyBoolFieldFormatter(BoolFieldFormatter):
    parse_null_values = True

    def parse(self, value: t.Any) -> bool:
        return bool(value)


class SortedJsonFormatter(FieldFormatter[JSON]):
    def parse(self, value: t.Any) -> JSON:
        # mypy seems to not handle this tuple passed to isinstance correctly
        if isinstance(
            value, (dict, list, int, str, float, None)  # type: ignore[arg-type]
        ):
            return t.cast(JSON, value)
        raise ValueError("bad JSON value")

    def render(self, value: JSON) -> str:
        return json.dumps(value, sort_keys=True)


Str = StrFieldFormatter()
Date = DateFieldFormatter()
Bool = BoolFieldFormatter()
FuzzyBool = FuzzyBoolFieldFormatter()
SortedJson = SortedJsonFormatter()
