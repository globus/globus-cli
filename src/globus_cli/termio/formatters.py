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
        """
        The `parse()` step is responsible for producing well-formed data for a field.
        For example, parsing may convert a dictionary or mapping to a tuple by pulling
        out the relevant fields and checking their types.

        If parsing fails for any reason, it should raise a ValueError.
        """

    @abc.abstractmethod
    def render(self, value: T) -> str:
        """
        The `render()` step is responsible taking data which has already been parsed
        and reshaped and converting it into a string.
        For example, rendering may comma-join an array of strings into a
        comma-delimited list.

        If rendering fails for any reason, it should raise a ValueError.
        """

    def format(self, value: t.Any) -> str:
        """
        Formatting data consists primarily of parsing and then rendering.
        If either step fails, the default behavior warns and falls back on str().
        """
        if value is None and self.parse_null_values is False:
            return "None"
        try:
            data = self.parse(value)
            return self.render(data)
        except ValueError:
            self.warn_formatting_failed(value)
            return str(value)


class StrFormatter(FieldFormatter[str]):
    def parse(self, value: t.Any) -> str:
        return str(value)

    def render(self, value: str) -> str:
        return value


class DateFormatter(FieldFormatter[datetime.datetime]):
    def parse(self, value: t.Any) -> datetime.datetime:
        return datetime.datetime.fromisoformat(value)

    def render(self, value: datetime.datetime) -> str:
        if value.tzinfo is None:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return value.astimezone().strftime("%Y-%m-%d %H:%M:%S")


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


class StaticStringFormatter(StrFormatter):
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
            element_formatter if element_formatter is not None else StrFormatter()
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
        parsed_type, parsed_value, fallback = value
        if parsed_type == "identity":
            try:
                return t.cast(str, self.resolved_ids[parsed_value]["username"])
            except LookupError:
                return parsed_value
        elif parsed_type == "group":
            return self.group_format_str.format(group_id=parsed_value)
        else:
            return fallback


# IdentityFormatters work over (principal, is_valid) tuples so that subclasses can
# override parse() to opt-out of the identity lookups in the render() phase
class IdentityFormatter(FieldFormatter[t.Tuple[str, bool]]):
    def __init__(self, auth_client: globus_sdk.AuthClient):
        self.auth_client = auth_client
        self.resolved_ids = globus_sdk.IdentityMap(auth_client)

    def parse(self, value: t.Any) -> tuple[str, bool]:
        if not isinstance(value, str):
            raise ValueError("non-str identity value")
        return (value, True)

    def render(self, value: tuple[str, bool]) -> str:
        principal, is_valid = value

        if is_valid:
            try:
                return t.cast(str, self.resolved_ids[principal]["username"])
            except LookupError:
                pass
        return principal


class IdentityURNFormatter(IdentityFormatter):
    _urn_prefix = "urn:globus:auth:identity:"

    def parse(self, value: t.Any) -> tuple[str, bool]:
        if not isinstance(value, str):
            raise ValueError("non-str identity value")
        if value.startswith(self._urn_prefix):
            return (value[len(self._urn_prefix) :], True)
        return (value, False)


class ParentheticalDescriptionFormatter(FieldFormatter[t.Tuple[str, str]]):
    def parse(self, value: t.Any) -> tuple[str, str]:
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError(
                "cannot format parenthetical description from data of wrong shape"
            )
        main, description = value[0], value[1]
        if not isinstance(main, str) or not isinstance(description, str):
            raise ValueError("cannot format parenthetical description non-str data")
        return (main, description)

    def render(self, value: tuple[str, str]) -> str:
        return f"{value[0]} ({value[1]})"


Str = StrFormatter()
Date = DateFormatter()
Bool = BoolFormatter()
FuzzyBool = FuzzyBoolFormatter()
SortedJson = SortedJsonFormatter()
Array = ArrayFormatter()
SortedArray = ArrayFormatter(sort=True)
