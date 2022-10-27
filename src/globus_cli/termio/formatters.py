from __future__ import annotations

import abc
import datetime
import json
import typing as t
import warnings

import globus_sdk

T = t.TypeVar("T")
JSON = t.Union[dict, list, str, int, float, bool, None]

_IDENTITY_URN_PREFIX = "urn:globus:auth:identity:"
_GROUP_URN_PREFIX = "urn:globus:groups:id:"


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


class PrincipalFormatter(FieldFormatter[t.Tuple[str, str]]):
    """
    PrincipalFormatters work over (principal, type) tuples.

    a "principal" could be an identity ID, a group ID, an identity URN, or a
        special-cased value

    a "type" is typically a well-known string which instructs the formatter how to
        do rendering like "group" or "identity"

    The base class defines three rendering cases:
      - identity
      - group
      - fallback
    """

    def __init__(self, auth_client: globus_sdk.AuthClient):
        self.auth_client = auth_client
        self.resolved_ids = globus_sdk.IdentityMap(auth_client)

    def render_identity_id(self, identity_id: str) -> str:
        try:
            return t.cast(str, self.resolved_ids[identity_id]["username"])
        except LookupError:
            return identity_id

    def render_group_id(self, group_id: str) -> str:
        return f"Globus Group ({group_id})"

    def fallback_rendering(self, principal: str, principal_type: str) -> str:
        return principal

    # the base PrincipalFormatter cannot be instantiated because parse() is variable
    # by the exact type of data being read
    @abc.abstractmethod
    def parse(self, value: t.Any) -> tuple[str, str]:
        ...

    def add_item(self, value: t.Any) -> None:
        try:
            principal, principal_type = self.parse(value)
        except ValueError:
            pass
        else:
            if principal_type == "identity":
                self.resolved_ids.add(principal)

    def render(self, value: tuple[str, str]) -> str:
        principal, principal_type = value

        if principal_type == "identity":
            return self.render_identity_id(principal)
        elif principal_type == "group":
            return self.render_group_id(principal)
        else:
            return self.fallback_rendering(principal, principal_type)


class IdentityStrFormatter(PrincipalFormatter):
    def parse(self, value: t.Any) -> tuple[str, str]:
        if not isinstance(value, str):
            raise ValueError("non-str identity value")
        return (value, "identity")


class PrincipalURNFormatter(PrincipalFormatter):
    def parse(self, value: t.Any) -> tuple[str, str]:
        if not isinstance(value, str):
            raise ValueError("non-str principal URN value")
        if value.startswith(_IDENTITY_URN_PREFIX):
            return (value[len(_IDENTITY_URN_PREFIX) :], "identity")
        if value.startswith(_GROUP_URN_PREFIX):
            return (value[len(_GROUP_URN_PREFIX) :], "group")
        return (value, "fallback")


class PrincipalDictFormatter(PrincipalFormatter):
    def parse(self, value: t.Any) -> tuple[str, str]:
        if not isinstance(value, dict):
            raise ValueError("cannot format principal from non-dict data")

        principal = t.cast(str, value["principal"])
        principal_type = t.cast(str, value["principal_type"])
        if principal_type in ("identity", "group"):
            return (principal, principal_type)
        return (principal, "fallback")


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
