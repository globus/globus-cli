from __future__ import annotations

import collections
import enum
import functools
import shutil
import typing as t

import click

from ..context import out_is_terminal, term_is_interactive
from ..field import Field
from .base import Printer


class OutputStyle(enum.Flag):
    none = enum.auto()
    decorated = enum.auto()
    heavy = enum.auto()
    top = enum.auto()
    bottom = enum.auto()


class FoldedTablePrinter(Printer[t.Iterable[t.Any]]):
    """
    A printer to render an iterable of objects holding tabular data with cells folded
    together and stacked in the format:

    .--------------------------------------------------.
    | <field.name 1> | <field.name 3> | <field.name 5> |
    | <field.name 2> | <field.name 4> |                |
    +================+================+================+
    | <obj.value 1>  | <obj.value 3>  | <obj.value 5>  |
    | <obj.value 2>  | <obj.value 4>  |                |
    +----------------+----------------+----------------+
    | <obj.value 1>  | <obj.value 3>  | <obj.value 5>  |
    | <obj.value 2>  | <obj.value 4>  |                |
    '----------------+----------------+----------------'

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

        table = self._fold_table(RowTable.from_data(self._fields, data))
        col_widths = table.calculate_column_widths()

        # if folded, print a leading separator line
        table_style = OutputStyle.decorated if table.folded else OutputStyle.none
        if table.folded:
            echo(_separator_line(col_widths, style=table_style | OutputStyle.top))
        # print the header row and a separator (heavy if folded)
        echo(table.header_row.serialize(col_widths, style=table_style))
        echo(
            _separator_line(
                col_widths,
                style=(
                    table_style
                    | (OutputStyle.heavy if table.folded else OutputStyle.none)
                ),
            )
        )

        for row in table.rows[1:-1]:
            echo(row.serialize(col_widths, style=table_style))
            if table.folded:
                echo(_separator_line(col_widths, style=table_style))
        echo(table.rows[-1].serialize(col_widths, style=table_style))
        if table.folded:
            echo(_separator_line(col_widths, style=table_style | OutputStyle.bottom))

    def _fold_table(self, table: RowTable) -> RowTable:
        if not _detect_folding_enabled():
            return table

        # if the table is initially narrow enough to fit, do not fold
        if table.fits_in_width(self._width):
            return table

        # try folding the table in half, and see if that fits
        folded_table = table.fold_rows(2)
        if folded_table.fits_in_width(self._width):
            return folded_table
        # if it's still too wide, fold in thirds and check that
        else:
            folded_table = table.fold_rows(3)
            if folded_table.fits_in_width(self._width):
                return folded_table
            # if folded by thirds does not fit, fold all the way to a single column
            else:
                return table.fold_rows(table.num_columns)


@functools.cache
def _separator_line(
    col_widths: tuple[int, ...], style: OutputStyle = OutputStyle.none
) -> str:
    fill = "=" if style & OutputStyle.heavy else "-"

    if style & OutputStyle.decorated:
        decorator = "+"
        if style & OutputStyle.top:
            decorator = "."
        elif style & OutputStyle.bottom:
            decorator = "'"

        leader = f"{decorator}{fill}"
        trailer = f"{fill}{decorator}"
    else:
        leader = ""
        trailer = ""

    line_parts = [leader]
    for col in col_widths[:-1]:
        line_parts.append(col * fill)
        line_parts.append(f"{fill}+{fill}")
    line_parts.append(col_widths[-1] * fill)
    line_parts.append(trailer)
    return "".join(line_parts)


class RowTable:
    """
    A data structure to hold tabular data which has not yet been laid out.

    :param rows: a list of rows with table's contents, including the header row
    :param folded: whether or not the table has been folded at all
    :raises ValueError: if any rows have different numbers of columns.
    """

    def __init__(self, rows: tuple[Row, ...], folded: bool = False) -> None:
        self.rows = rows
        self.folded = folded

        self.num_columns = rows[0].num_cols
        self.num_rows = len(rows)

    @property
    def header_row(self) -> Row:
        return self.rows[0]

    def fits_in_width(self, width: int) -> bool:
        return all(x.min_rendered_width <= width for x in self.rows)

    def fold_rows(self, n: int) -> RowTable:
        """Produce a new table with folded rows."""
        return RowTable(tuple(cell.fold(n) for cell in self.rows), folded=True)

    def calculate_column_widths(self) -> tuple[int, ...]:
        return tuple(
            max(0, *(self.rows[row].column_widths[col] for row in range(self.num_rows)))
            for col in range(self.rows[0].num_cols)
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
        if self.is_folded:
            raise ValueError(
                "Rows can only be folded once. Use the original row to refold."
            )
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
    def is_folded(self) -> bool:
        return len(self.grid) > 1

    @functools.cached_property
    def min_rendered_width(self) -> int:
        decoration_length = 0
        if self.is_folded:
            decoration_length = 4
        return sum(self.column_widths) + (3 * (self.num_cols - 1)) + decoration_length

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

    def serialize(
        self, use_col_widths: tuple[int, ...], style: OutputStyle = OutputStyle.none
    ) -> str:
        lines: list[str] = []
        for subrow in self.grid:
            new_line: list[str] = []
            for idx, width in enumerate(use_col_widths):
                new_line.append((subrow[idx] if idx < len(subrow) else "").ljust(width))

            if style & OutputStyle.decorated:
                leader = "| "
                trailer = " |"
            else:
                leader = ""
                trailer = ""
            lines.append(leader + " | ".join(new_line) + f"{trailer}")
        return "\n".join(lines)


def _get_terminal_content_width() -> int:
    """Get a content width for text output based on the terminal size.

    Uses the 90% of terminal width, if it can be detected.
    """
    cols = shutil.get_terminal_size(fallback=(80, 20)).columns
    return cols if cols < 88 else int(0.9 * cols)


def _detect_folding_enabled() -> bool:
    return out_is_terminal() and term_is_interactive()
