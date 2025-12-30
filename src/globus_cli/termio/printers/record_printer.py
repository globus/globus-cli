from __future__ import annotations

import functools
import shutil
import typing as t
from textwrap import TextWrapper

import click
import globus_sdk

from globus_cli.types import JsonValue

from ..field import Field
from .base import Printer

DataObject = t.Union[JsonValue, globus_sdk.GlobusHTTPResponse]


class RecordPrinter(Printer[DataObject]):
    """
    Prints data objects in the form:

    key1:      value1
    long-key2: value2
    key3:      value3 which is so long that it must wrap around onto
               the next line
    key4:      value4

    :param fields: a collection of Fields with load and render instructions; one per
        attribute.
    :param max_width: the maximum width of the output. Defaults to 80% of the terminal
        width.
    """

    def __init__(
        self, fields: t.Iterable[Field], *, max_width: int | None = None
    ) -> None:
        self._fields = list(fields)
        self._item_wrapper = TextWrapper(
            initial_indent=" " * self._key_len,
            subsequent_indent=" " * self._key_len,
            width=max_width or _get_terminal_content_width(),
        )

    def echo(self, data: DataObject, stream: t.IO[str] | None = None) -> None:
        for field in self._fields:
            item = self._format_item(data, field)
            click.echo(item, file=stream)

    def _format_item(self, data: DataObject, field: Field) -> str:
        """Format a single key-value pair into a string."""
        key = f"{field.name}:".ljust(self._key_len)
        value = field.serialize(data)

        if field.wrap_enabled:
            value = self._wrap_value(value)
        return f"{key}{value}"

    def _wrap_value(self, value: str) -> str:
        """
        Wrap a value string to fit in the terminal width.
        *  Every subsequent line is indented to match the key column width.
        *  Hardcoded newlines are preserved
        *  After 5 lines of wrapping, the value is truncated with "..."

        Example responses: (screen width: 8, key width: 4):
        _wrap_value("aaaa bbbb") ->
        "aaaa"
        "    bbbb"

        _wrap_value("aaa\na bbbb") ->
        "aaa"
        "    a"
        "    bbbb"
        """
        wrapped_lines = []
        for line in value.splitlines():
            wrapped_lines.extend(self._item_wrapper.wrap(line))

        if len(wrapped_lines) > 5:
            wrapped_lines = wrapped_lines[:5] + self._item_wrapper.wrap("...")

        wrapped_value = "\n".join(wrapped_lines)
        return wrapped_value[self._key_len :]

    @functools.cached_property
    def _key_len(self) -> int:
        """The number of chars in the key column."""
        return max(len(f.name) for f in self._fields) + 2


class RecordListPrinter(Printer[t.Iterable[DataObject]]):
    """
    A printer to render an iterable of data objects as a series of records in the form:


    key1:      obj1.value1
    long-key2: obj1.value2
    key3:      obj1.value3 which is so long that it must wrap around onto
               the next line

    key1:      obj2.value1
    long-key2: obj2.value2
    key3:      obj2.value3

    :param fields: a collection of Fields with load and render instructions; one per
        attribute.
    :param max_width: the maximum width of the output. Defaults to 80% of the terminal
        width.
    """

    def __init__(
        self, fields: t.Iterable[Field], *, max_width: int | None = None
    ) -> None:
        self._record_printer = RecordPrinter(fields, max_width=max_width)

    def echo(
        self,
        data: t.Iterable[DataObject],
        stream: t.IO[str] | None = None,
    ) -> None:
        prepend_newline = False
        for item in data:
            if prepend_newline:
                click.echo("", file=stream)
            prepend_newline = True

            self._record_printer.echo(item, stream)


def _get_terminal_content_width() -> int:
    """Get a content width for text output based on the terminal size.

    Uses 80% of the terminal width, if it can be detected and isn't too small.
    """
    cols = shutil.get_terminal_size(fallback=(80, 20)).columns
    return cols if cols < 100 else int(0.8 * cols)
