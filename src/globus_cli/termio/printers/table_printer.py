from __future__ import annotations

import functools
import typing as t

import click

from .base import Printer

if t.TYPE_CHECKING:
    from ..field import Field


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

    def echo(self, data: t.Iterable[t.Any], stream: t.IO[str] | None = None) -> None:
        """
        Print out a rendered table.

        :param data: an iterable of data objects.
        :param stream: an optional IO stream to write to. Defaults to stdout.
        """
        echo = functools.partial(click.echo, file=stream)
        table = DataTable.from_data(self._fields, data)

        if self._print_headers:
            echo(self._serialize_row(table, self._headers))
            echo(self._serialize_row(table, fillchar="-"))

        for y in range(table.num_rows):
            values = [table[x, y] for x in range(table.num_columns)]
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

    @functools.lru_cache(maxsize=None)  # noqa: B019
    def _column_width(self, table: DataTable, x: int) -> int:
        """The width of a column in the table."""
        values = [table[x, y] for y in range(table.num_rows)]
        if self._print_headers:
            values.append(self._headers[x])

        return max(0, *(len(value) for value in values))


class DataTable:
    """
    A data structure to hold tabular data in a 2D grid of cells.

    This class only models data cells; other table elements like headers are not
    persisted and must be handled separately.

    :param cells: a 2D tuple of strings with table's cell data.
    :raises ValueError: if any rows have different numbers of columns.
    """

    def __init__(self, cells: tuple[tuple[str, ...], ...]) -> None:
        self._cells = cells

        for row in cells:
            if len(row) != len(cells[0]):
                raise ValueError("All rows must have the same number of columns.")

        self.num_columns = len(cells[0])
        self.num_rows = len(cells)

    @classmethod
    def from_data(cls, fields: tuple[Field, ...], data: t.Iterable[t.Any]) -> DataTable:
        """
        Create a DataTable from a list of fields and iterable of data objects.

        The data objects are serialized and discarded upon creation.
        """
        rows = []
        for data_obj in data:
            row = tuple(field.serialize(data_obj) for field in fields)
            rows.append(tuple(row))

        return cls(tuple(rows))

    def __getitem__(self, key: tuple[int, int]) -> str:
        """
        Get the value of a cell in the table.

        :param key: A tuple of two values (column index, row index).
        :return: A string representation of the cell's value.
        :raises IndexError: if either index is out of range.
        """
        x, y = key
        if x < 0 or x >= self.num_columns:
            raise IndexError(f"Table column index out of range: {x}")
        if y < 0 or y >= self.num_rows:
            raise IndexError(f"Table row index out of range: {y}")
        return self._cells[y][x]
