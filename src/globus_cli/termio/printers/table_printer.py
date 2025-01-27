from __future__ import annotations

import functools
import typing as t

import click

from ..field import Field
from .base import Printer


class TablePrinter(Printer[t.Iterable[t.Any]]):
    """
    A printer to render an iterable of objects holding tabular data in the format:

    <field.name 1> | <field.name 2> | ... | <field.name N>
    -------------- | -------------- | ... | --------------
    <obj1.value 1> | <obj1.value 2> | ... | <obj1.value N>

    :param fields: a list of Fields with load and render instructions; one per column.
    :param print_headers: if False, omit the header row & separator row.
    """

    def __init__(
        self, fields: t.Iterable[Field], *, print_headers: bool = True
    ) -> None:
        self._fields = tuple(fields)
        self._print_headers = print_headers

    def print(self, data: t.Iterable[t.Any], stream: t.IO[str] | None = None) -> None:
        """
        Print out a rendered table.

        :param data: an iterable of data objects.
        :param stream: an optional IO stream to write to. Defaults to stdout.
        """
        echo = functools.partial(click.echo, file=stream)
        table = DataTable(self._fields, data)

        if self._print_headers:
            echo(self._serialize_row(table, self._headers))
            echo(self._serialize_row(table, fillchar="-"))

        for y in range(table.num_rows):
            values = [table.cell(x, y) for x in range(table.num_columns)]
            echo(self._serialize_row(table, values))

    @functools.cached_property
    def _headers(self) -> tuple[str, ...]:
        """A tuple of header strings."""
        return tuple(field.name for field in self._fields)

    def _serialize_row(
        self,
        table: DataTable,
        values: t.Iterable[str] | None = None,
        *,
        fillchar: str = " ",
    ) -> str:
        """
        Serialize a row of values into a pipe-delimited string of cells.

        :param table: the table object containing the data.
        :param values: a list of values to serialize. If None; a row of empty cells is
            created.
        :param fillchar: the character to use in padding cells.
        """
        cells = []
        if values is None:
            values = [""] * table.num_columns

        for x, value in enumerate(values):
            width = self._column_width(table, x)
            cells.append(value.ljust(width, fillchar))
        return " | ".join(cells)

    @functools.lru_cache(maxsize=16)  # noqa: B019
    def _column_width(self, table: DataTable, x: int) -> int:
        """The width of a column in the table."""
        values = [table.cell(x, y) for y in range(table.num_rows)]
        if self._print_headers:
            values.append(self._headers[x])

        return max(0, *(len(value) for value in values))


class DataTable:
    def __init__(self, fields: tuple[Field, ...], data: t.Iterable[t.Any]) -> None:
        self._fields = fields
        self._data = tuple(data)

        self.num_columns = len(fields)
        self.num_rows = len(self._data)

    @functools.lru_cache(maxsize=256)  # noqa: B019
    def cell(self, x: int, y: int) -> str:
        """
        Get the value of a cell in the table.

        Note: This class only models data cells; other table elements like headers
              are not represented and should be handled separately.
        :param x: A 0-based column index.
        :param y: A 0-based row index.
        :return: A string representation of the cell's value.
        :raises IndexError: if either index is out of range.
        """
        if x >= len(self._fields):
            raise IndexError(
                f"Column index out of range. (Index: {x}; Length: {len(self._fields)})"
            )
        if y >= len(self._data):
            raise IndexError(
                f"Row index out of range. (Index: {y}; Length: {len(self._data)})"
            )
        field = self._fields[x]
        data_obj = self._data[y]

        return field.serialize(data_obj)
