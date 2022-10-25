from __future__ import annotations

import abc
import datetime
import json
import typing as t
import warnings

import globus_sdk

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


class StaticStringFormatter(StrFieldFormatter):
    def __init__(self, value: str) -> None:
        self.value = value

    def parse(self, value: t.Any) -> str:
        return self.value


class ArrayFormatter(FieldFormatter[t.List[str]]):
    def __init__(
        self,
        *,
        delimiter: str = ",",
        sort: bool = False,
        element_formatter: FieldFormatter | None = None,
    ) -> None:
        self.delimiter = delimiter
        self.sort = sort
        self.element_formatter: FieldFormatter = (
            element_formatter if element_formatter is not None else StrFieldFormatter()
        )

    def parse(self, value: t.Any) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("non list array value")
        data = [self.element_formatter.format(x) for x in value]
        if self.sort:
            return sorted(data)
        else:
            return data

    def render(self, value: list[str]) -> str:
        return self.delimiter.join(value)


class PrincipalWithTypeKeyFormatter(FieldFormatter[t.Tuple[str, str, str]]):
    def __init__(
        self,
        auth_client: globus_sdk.AuthClient,
        *,
        type_key: str = "principal_type",
        value_key: str = "principal",
        values_are_urns: bool = True,
        group_format_str: str = "Globus Group ({group_id})",
    ) -> None:
        self.type_key = type_key
        self.value_key = value_key
        self.values_are_urns = values_are_urns
        self.group_format_str = group_format_str
        self.resolved_ids = globus_sdk.IdentityMap(auth_client)

    def _parse_unresolved_principal(self, value: str) -> str:
        if self.values_are_urns:
            return value.split(":")[-1]
        return value

    def add_items(self, items: t.Iterable[t.Mapping[str, t.Any]]) -> None:
        for x in items:
            if x.get(self.type_key) != "identity":
                continue
            self.resolved_ids.add(
                self._parse_unresolved_principal(t.cast(str, x[self.value_key]))
            )

    def parse(self, value: t.Any) -> tuple[str, str, str]:
        if not isinstance(value, dict):
            raise ValueError("cannot format principal from non-dict data")

        unparsed_principal = t.cast(str, value[self.value_key])

        return (
            value[self.type_key],
            self._parse_unresolved_principal(unparsed_principal),
            unparsed_principal,
        )

    def render(self, value: tuple[str, str, str]) -> str:
        ptype, pvalue, unparsed = value
        if ptype == "identity":
            try:
                return t.cast(str, self.resolved_ids[pvalue]["username"])
            except LookupError:
                return pvalue
        elif ptype == "group":
            return self.group_format_str.format(group_id=pvalue)
        else:
            return unparsed


Str = StrFieldFormatter()
Date = DateFieldFormatter()
Bool = BoolFieldFormatter()
FuzzyBool = FuzzyBoolFieldFormatter()
SortedJson = SortedJsonFormatter()
Array = ArrayFormatter()
SortedArray = ArrayFormatter(sort=True)
