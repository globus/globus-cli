from __future__ import annotations

import collections
import functools
import shutil
import typing as t

import click

from ..field import Field
from .base import Printer


class FoldedTablePrinter(Printer[t.Iterable[t.Any]]):
    """
    A printer to render an iterable of objects holding tabular data with cells folded
    together and stacked in the format:

    +--------------------------------------------------+
    | <field.name 1> | <field.name 3> | <field.name 5> |
    | <field.name 2> | <field.name 4> |                |
    +==================================================+
    | <obj.value 1>  | <obj.value 3>  | <obj.value 5>  |
    | <obj.value 2>  | <obj.value 4>  |                |
    +--------------------------------------------------+
    | <obj.value 1>  | <obj.value 3>  | <obj.value 5>  |
    | <obj.value 2>  | <obj.value 4>  |                |
    +--------------------------------------------------+

    Rows are folded and stacked only if they won't fit in the output width.

    :param fields: a list of Fields with load and render instructions; one per column.
    """

    def __init__(self, fields: t.Iterable[Field]) -> None:
        self._fields = tuple(fields)
        self._width = _get_terminal_content_width()

    def echo(self, data: t.Iterable[t.Any], stream: t.IO[str] | None = None) -> None:
        """
        Print out a rendered table.

        :param data: an iterable of data objects.
        :param stream: an optional IO stream to write to. Defaults to stdout.
        """
        echo = functools.partial(click.echo, file=stream)

        table = RowTable.from_data(self._fields, data)

        # ----- Main Table Folding Rules -----
        # if the table is too wide
        if not table.fits_in_width(self._width):
            # try folding the table in half, and see if that fits
            folded_table = table.fold_rows(2)
            if folded_table.fits_in_width(self._width):
                table = folded_table
            # if it's still too wide, fold in thirds and check that
            else:
                folded_table = table.fold_rows(3)
                if folded_table.fits_in_width(self._width):
                    table = folded_table
                # if folded by thirds does not fit, fold all the way to a single column
                else:
                    table = table.fold_rows(table.num_columns)

        col_widths = table.calculate_column_widths()

        echo(_separator_line(col_widths))
        echo(table.header_row.serialize(col_widths))
        echo(_separator_line(col_widths, heavy=True))

        for row in table.cells[1:]:
            echo(row.serialize(col_widths))
            echo(_separator_line(col_widths))


@functools.cache
def _separator_line(col_widths: tuple[int, ...], heavy: bool = False) -> str:
    fill = "-"
    if heavy:
        fill = "="

    #                                         .--- 3 spaces between columns
    #              .--- total rendered width |                   .--- one space at each
    #             v                          v                  v     end
    fill_length = sum(col_widths) + 3 * (len(col_widths) - 1) + 2
    return "+" + (fill_length * fill) + "+"


class RowTable:
    """
    A data structure to hold tabular data which has not yet been laid out.

    This class only models data cells; other table elements like headers are not
    persisted and must be handled separately.

    :param cells: a list of rows with table's cell data.
    :raises ValueError: if any rows have different numbers of columns.
    """

    def __init__(self, cells: tuple[Row, ...]) -> None:
        self.cells = cells

        for row in cells:
            if len(row) != len(cells[0]):
                raise ValueError("All rows must have the same number of columns.")

        self.num_columns = cells[0].num_cols
        self.num_rows = len(cells)

    @property
    def header_row(self) -> Row:
        return self.cells[0]

    def fits_in_width(self, width: int) -> bool:
        return all(x.min_rendered_width <= width for x in self.cells)

    def fold_rows(self, n: int) -> RowTable:
        """Produce a new table with folded rows."""
        return RowTable(tuple(cell.fold(n) for cell in self.cells))

    def calculate_column_widths(self) -> tuple[int, ...]:
        return tuple(
            max(
                0, *(self.cells[row].column_widths[col] for row in range(self.num_rows))
            )
            for col in range(self.cells[0].num_cols)
        )

    @classmethod
    def from_data(cls, fields: tuple[Field, ...], data: t.Iterable[t.Any]) -> RowTable:
        """
        Create a RowTable from a list of fields and iterable of data objects.

        The data objects are serialized and discarded upon creation.
        """
        rows = []
        # insert the header row
        rows.append(Row((tuple(f.name for f in fields),)))
        for data_obj in data:
            rows.append(Row.from_source_data(fields, data_obj))

        return cls(tuple(rows))


class Row:
    """A semantic row in the table of output, with a gridded internal layout."""

    def __init__(self, grid: tuple[tuple[str, ...], ...]) -> None:
        self.grid: tuple[tuple[str, ...], ...] = grid

    def __len__(self) -> int:
        return sum(len(subrow) for subrow in self.grid)

    def __getitem__(self, coords: tuple[int, int]) -> str:
        subrow, col = coords
        return self.grid[subrow][col]

    @classmethod
    def from_source_data(cls, fields: tuple[Field, ...], source: t.Any) -> Row:
        return cls((tuple(field.serialize(source) for field in fields),))

    def fold(self, n: int) -> Row:
        """Fold the internal grid by N, stacking elements. Produces a new Row."""
        if len(self.grid) > 1:
            raise ValueError("Rows can only be folded once. Use the original row.")
        return Row(tuple(self._split_level(self.grid[0], n)))

    def _split_level(
        self, level: tuple[str, ...], modulus: int
    ) -> t.Iterator[tuple[str, ...], ...]:
        bins = collections.defaultdict(list)
        for i, x in enumerate(level):
            bins[i % modulus].append(x)

        for i in range(modulus):
            yield tuple(bins[i])

    @functools.cached_property
    def min_rendered_width(self) -> int:
        return sum(self.column_widths) + (2 * self.num_cols) + 2

    @functools.cached_property
    def num_cols(self) -> int:
        return max(0, *(len(subrow) for subrow in self.grid))

    @functools.cached_property
    def column_widths(self) -> tuple[int, ...]:
        """The width of all columns in the row (as measured in this row)."""
        return tuple(self._calculate_col_width(i) for i in range(self.num_cols))

    def _calculate_col_width(self, idx: int) -> int:
        return max(
            0, *(len(subrow[idx]) if idx < len(subrow) else 0 for subrow in self.grid)
        )

    def serialize(self, use_col_widths: tuple[int, ...]) -> str:
        lines: list[str] = []
        for subrow in self.grid:
            new_line: list[str] = []
            for idx, width in enumerate(use_col_widths):
                new_line.append((subrow[idx] if idx < len(subrow) else "").ljust(width))
            lines.append("| " + " | ".join(new_line) + " |\n")
        return "".join(lines).rstrip("\n")


def _get_terminal_content_width() -> int:
    """Get a content width for text output based on the terminal size.

    Uses the 90% of terminal width, if it can be detected.
    """
    cols = shutil.get_terminal_size(fallback=(80, 20)).columns
    return cols if cols < 88 else int(0.9 * cols)
