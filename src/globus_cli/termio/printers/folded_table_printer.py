from __future__ import annotations

import collections
import dataclasses
import enum
import functools
import shutil
import typing as t

import click

from ..context import out_is_terminal, term_is_interactive
from ..field import Field
from .base import Printer


# the separator rows, including the top and bottom
class SeparatorRowType(enum.Enum):
    # top of a table
    box_top = enum.auto()
    # between the header and the rest of the table (box drawing chars)
    box_header_separator = enum.auto()
    # the same, but for ASCII tables
    ascii_header_separator = enum.auto()
    # between rows of the table
    box_row_separator = enum.auto()
    # between element lines inside of a row of a table
    box_intra_row_separator = enum.auto()
    # bottom of a table
    box_bottom = enum.auto()


@dataclasses.dataclass
class SeparatorRowStyle:
    fill: str
    leader: str
    trailer: str
    middle: str


SEPARATOR_ROW_STYLE_CHART: dict[SeparatorRowType, SeparatorRowStyle] = {
    SeparatorRowType.ascii_header_separator: SeparatorRowStyle(
        fill="-", leader="", trailer="", middle="+"
    ),
    SeparatorRowType.box_top: SeparatorRowStyle(
        fill="═", leader="╒═", trailer="═╕", middle="╤"
    ),
    SeparatorRowType.box_header_separator: SeparatorRowStyle(
        fill="═", leader="╞═", trailer="═╡", middle="╪"
    ),
    SeparatorRowType.box_row_separator: SeparatorRowStyle(
        fill="─", leader="├─", trailer="─┤", middle="┼"
    ),
    SeparatorRowType.box_intra_row_separator: SeparatorRowStyle(
        fill="─", leader="├─", trailer="─┤", middle="┼"
    ),
    SeparatorRowType.box_bottom: SeparatorRowStyle(
        fill="─", leader="└─", trailer="─┘", middle="┴"
    ),
}


class FoldedTablePrinter(Printer[t.Iterable[t.Any]]):
    """
    A printer to render an iterable of objects holding tabular data with cells folded
    together and stacked in the format:

    ╒════════════════╤════════════════╤════════════════╕
    │ <field.name 1> ╎ <field.name 3> ╎ <field.name 5> │
    ├─ ─ ─ ─ ─ ─ ─  ─┼─ ─ ─ ─ ─ ─ ─  ─┼─ ─ ─ ─ ─ ─ ─  ─┤
    │ <field.name 2> ╎ <field.name 4> ╎                │
    ╞════════════════╪════════════════╪════════════════╡
    │ <obj.value 1>  ╎ <obj.value 3>  ╎ <obj.value 5>  │
    ├─ ─ ─ ─ ─ ─ ─  ─┼─ ─ ─ ─ ─ ─ ─  ─┼─ ─ ─ ─ ─ ─ ─  ─┤
    │ <obj.value 2>  ╎ <obj.value 4>  ╎                │
    ├────────────────┼────────────────┼────────────────┤
    │ <obj.value 1>  ╎ <obj.value 3>  ╎ <obj.value 5>  │
    ├─ ─ ─ ─ ─ ─ ─  ─┼─ ─ ─ ─ ─ ─ ─  ─┼─ ─ ─ ─ ─ ─ ─  ─┤
    │ <obj.value 2>  ╎ <obj.value 4>  ╎                │
    └────────────────┴────────────────┴────────────────┘

    Rows are folded and stacked only if they won't fit in the output width.

    :param fields: a list of Fields with load and render instructions; one per column.
    """

    def __init__(self, fields: t.Iterable[Field], width: int | None = None) -> None:
        self._fields = tuple(fields)
        self._width = width or _get_terminal_content_width()
        self._folding_enabled = _detect_folding_enabled()

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
        if table.folded:
            echo(_separator_line(col_widths, row_type=SeparatorRowType.box_top))
        # print the header row and a separator
        echo(table.header_row.serialize(col_widths))
        echo(
            _separator_line(
                col_widths,
                row_type=(
                    SeparatorRowType.box_header_separator
                    if table.folded
                    else SeparatorRowType.ascii_header_separator
                ),
            )
        )

        for row in table.content_rows[:-1]:
            echo(row.serialize(col_widths))
            if table.folded:
                echo(
                    _separator_line(
                        col_widths,
                        row_type=SeparatorRowType.box_row_separator,
                    )
                )
        # it is possible for a table to be empty, so check before attempting to
        # serialize the last row
        if table.content_rows:
            echo(table.content_rows[-1].serialize(col_widths))
        if table.folded:
            echo(_separator_line(col_widths, row_type=SeparatorRowType.box_bottom))

    def _fold_table(self, table: RowTable) -> RowTable:
        if not self._folding_enabled:
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

    @property
    def content_rows(self) -> tuple[Row, ...]:
        return self.rows[1:]

    def fits_in_width(self, width: int) -> bool:
        return self.calculate_width() <= width

    def calculate_width(self) -> int:
        """
        For each column, find the row where that column is the max width.
        Sum those widths + the width of the separators (3 * (ncols-1))
        """
        max_widths = []
        for idx in range(self.num_columns):
            max_widths.append(max(row.column_widths[idx] for row in self.rows))

        decoration_length = 0
        if self.folded:
            decoration_length = 4

        return sum(max_widths) + (3 * (self.num_columns - 1)) + decoration_length

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
    ) -> t.Iterator[tuple[str, ...]]:
        bins = collections.defaultdict(list)
        for i, x in enumerate(level):
            bins[i % modulus].append(x)

        for i in range(modulus):
            yield tuple(bins[i])

    @functools.cached_property
    def is_folded(self) -> bool:
        return len(self.grid) > 1

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
        if len(self.grid) < 1:
            raise ValueError("Invalid state. Cannot serialize an empty row.")

        if len(self.grid) == 1:
            # format using ASCII characters (not folded)
            return _format_subrow(self.grid[0], use_col_widths, "|", "", "")

        lines: list[str] = []

        row_separator: str = _separator_line(
            use_col_widths, SeparatorRowType.box_intra_row_separator
        )
        for i, subrow in enumerate(self.grid):
            if i > 0:
                lines.append(row_separator)
            # format using box drawing characters (part of folded output)
            lines.append(_format_subrow(subrow, use_col_widths, "╎", "│ ", " │"))
        return "\n".join(lines)


def _format_subrow(
    subrow: tuple[str, ...],
    use_col_widths: tuple[int, ...],
    separator: str,
    leader: str,
    trailer: str,
) -> str:
    line: list[str] = []
    for idx, width in enumerate(use_col_widths):
        line.append((subrow[idx] if idx < len(subrow) else "").ljust(width))
    return leader + f" {separator} ".join(line) + trailer


@functools.cache
def _separator_line(col_widths: tuple[int, ...], row_type: SeparatorRowType) -> str:
    style = SEPARATOR_ROW_STYLE_CHART[row_type]

    # in intra-row separator lines, they are drawn as dashed box char lines
    if row_type is SeparatorRowType.box_intra_row_separator:
        fill_column: t.Callable[[int], str] = _draw_dashed_box_line
    # for all other cases, they're just a "flood fill" with the fill char
    else:

        def fill_column(width: int) -> str:
            return width * style.fill

    line_parts = [style.leader]
    for col in col_widths[:-1]:
        line_parts.append(fill_column(col))
        line_parts.append(f"{style.fill}{style.middle}{style.fill}")
    line_parts.append(fill_column(col_widths[-1]))
    line_parts.append(style.trailer)
    return "".join(line_parts)


@functools.cache
def _draw_dashed_box_line(width: int) -> str:
    # repeat with whitespace
    sep = " ─" * width
    sep = sep[:width]  # trim to length
    if sep[-1] == "─":  # ensure it ends in whitespace
        sep = sep[:-1] + " "
    return sep


def _get_terminal_content_width() -> int:
    """Get a content width for text output based on the terminal size.

    Uses the 90% of terminal width, if it can be detected.
    """
    cols = shutil.get_terminal_size(fallback=(80, 20)).columns
    return cols if cols < 88 else int(0.9 * cols)


def _detect_folding_enabled() -> bool:
    return out_is_terminal() and term_is_interactive()
