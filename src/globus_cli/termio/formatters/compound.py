from __future__ import annotations

import io
import json
import os
import textwrap
import typing as t

import globus_sdk

from globus_cli.types import JsonDict, JsonValue, is_json_dict

from ..printers import RecordPrinter
from .base import FieldFormatter
from .primitive import StrFormatter

if t.TYPE_CHECKING:
    from .. import Field


class SortedJsonFormatter(FieldFormatter[JsonValue]):
    """
    Example:
        in: {"b": 2, "a": 1}
        out: '{"a": 1, "b": 2}'
    """

    parse_null_values = True

    def parse(self, value: t.Any) -> JsonValue:
        if value is None or isinstance(value, (bool, dict, float, int, list, str)):
            return value
        raise ValueError("bad JsonValue value")

    def render(self, value: JsonValue) -> str:
        return json.dumps(value, sort_keys=True)


class ArrayFormatter(FieldFormatter[t.List[str]]):
    """
    Example:
        in:  ["a", "b", "c"]
        out: "a,b,c"
    """

    def __init__(
        self,
        *,
        delimiter: str = ",",
        sort: bool = False,
        element_formatter: FieldFormatter[t.Any] | None = None,
    ) -> None:
        self.delimiter = delimiter
        self.sort = sort
        self.element_formatter: FieldFormatter[t.Any] = (
            element_formatter if element_formatter is not None else StrFormatter()
        )

    def parse(self, value: t.Any) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("non list array value")
        data = [self.parse_element(element) for element in value]
        if self.sort:
            return sorted(data)
        else:
            return data

    def parse_element(self, element: t.Any) -> str:
        return self.element_formatter.format(element)

    def render(self, value: list[str]) -> str:
        return self.delimiter.join(value)


class ArrayMultilineFormatter(ArrayFormatter):
    """
    Example:
        in:  ["a", "b", "c\nd"]
        out: "  - a\n  - b\n  - c\n    d"
    """

    def __init__(self, formatter: FieldFormatter[t.Any] | None = None) -> None:
        super().__init__(delimiter=os.linesep, sort=False, element_formatter=formatter)

    def render(self, value: list[str]) -> str:
        prefix = os.linesep if value else ""
        return prefix + super().render(value)

    def parse_element(self, element: t.Any) -> str:
        formatted = self.element_formatter.format(element)
        return self._indent_element(formatted)

    @classmethod
    def _indent_element(cls, value: str) -> str:
        """Indent a multi-line formatted element string."""
        first_ = "  - "
        if not value:
            return first_
        indent = "    "
        indented = textwrap.indent(value, indent, lambda _: True)
        return first_ + indented[len(indent) :]


Record = t.Union[JsonDict, globus_sdk.GlobusHTTPResponse]


class RecordFormatter(FieldFormatter[Record]):
    """
    Note:
        This formatter is only tested with in a ``RecordPrinter`` and/or an
        ``ArrayMultilineFormatter``.

        Additional support for other printers/nested records should be added as needed.

    Example:
        in:  {"a": 1, "bb": 2}
        out: "a:  1\nbb: 2"
    """

    def __init__(self, fields: t.Iterable[Field]) -> None:
        self._fields = fields

    def _printer(self, reserved_width: int) -> RecordPrinter:
        """
        A RecordPrinter whose max content width is constrained by `reserved_width`.
          e.g., if the printer would naturally use a max of 20 chars but 2 are reserved,
            it will instead use a max of 18 chars.
        """
        max_content_width = RecordPrinter.default_max_content_width()
        reduced_max_content_width = max_content_width - reserved_width
        return RecordPrinter(self._fields, max_content_width=reduced_max_content_width)

    def parse(self, value: t.Any) -> Record:
        if not (
            isinstance(value, globus_sdk.GlobusHTTPResponse) or is_json_dict(value)
        ):
            raise ValueError("bad RecordFormatter value")

        for field in self._fields:
            if field.key not in value:
                raise ValueError(f"missing key {field.key} in dict")
        return value

    def render(self, value: Record) -> str:
        # How do we know how much width to reserve???
        printer = self._printer(reserved_width=2)

        with io.StringIO() as buffer:
            printer.echo(value, stream=buffer)
            # Materialize the buffer, stripping the trailing newline
            return buffer.getvalue().rstrip()


class ParentheticalDescriptionFormatter(FieldFormatter[t.Tuple[str, str]]):
    """
    Example:
       in:  ["state", "reason for state"]
       out: "state (reason for state)"
    """

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
