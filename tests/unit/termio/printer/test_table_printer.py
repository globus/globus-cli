from io import StringIO

import pytest

from globus_cli.termio import Field
from globus_cli.termio.printers import TablePrinter
from globus_cli.termio.printers.table_printer import DataTable


def test_table_printer_prints_with_headers():
    fields = (
        Field("Column A", "a"),
        Field("Column B", "b"),
        Field("Column C", "c"),
    )
    data = (
        {"a": 1, "b": 4, "c": 7},
        {"a": 2, "b": 5, "c": 8},
        {"a": 3, "b": 6, "c": 9},
    )
    printer = TablePrinter(fields=fields)

    with StringIO() as stream:
        printer.print(data, stream)
        printed_table = stream.getvalue()

    # fmt: off
    assert printed_table == (
        "Column A | Column B | Column C\n"
        "-------- | -------- | --------\n"
        "1        | 4        | 7       \n"
        "2        | 5        | 8       \n"
        "3        | 6        | 9       \n"
    )
    # fmt: on


def test_table_printer_prints_without_headers():
    fields = (
        Field("Column A", "a"),
        Field("Column B", "b"),
        Field("Column C", "c"),
    )
    data = (
        {"a": 1, "b": 4, "c": 7},
        {"a": 2, "b": 5, "c": 8},
        {"a": 3, "b": 6, "c": 9},
    )
    printer = TablePrinter(fields=fields, print_headers=False)

    with StringIO() as stream:
        printer.print(data, stream)
        printed_table = stream.getvalue()

    # fmt: off
    assert printed_table == (
        "1 | 4 | 7\n"
        "2 | 5 | 8\n"
        "3 | 6 | 9\n"
    )
    # fmt: on


def test_table_printer_computes_column_width():
    field = Field("Length is 12", "a")
    data = ({"a": "Length - 11"}, {"a": "Length: 10"})

    printer = TablePrinter(fields=(field,))
    table = DataTable.from_data(fields=(field,), data=data)

    assert printer._column_width(table, 0) == 12


def test_table_printer_computes_ignores_header_column_width_if_not_printed():
    field = Field("Length is 12", "a")
    data = ({"a": "Length - 11"}, {"a": "Length: 10"})

    printer = TablePrinter(fields=(field,), print_headers=False)
    table = DataTable.from_data(fields=(field,), data=data)

    # Header is length 12; but won't be printed; next highest is 11.
    assert printer._column_width(table, 0) == 11


def test_table_printer_ignores_extra_fields():
    fields = (Field("A", "a"), Field("B", "b"))
    data = (
        {"a": 1, "b": 2, "c": 3},
        {"a": 4, "b": 5},
    )

    printer = TablePrinter(fields=fields)

    with StringIO() as stream:
        printer.print(data, stream)
        printed_table = stream.getvalue()

    # fmt: off
    assert printed_table == (
        "A | B\n"
        "- | -\n"
        "1 | 2\n"
        "4 | 5\n"
    )
    # fmt: on


def test_table_printer_handles_missing_fields():
    fields = (Field("A", "a"), Field("B", "b"))
    data = (
        {"a": 1},
        {"b": 5},
    )

    printer = TablePrinter(fields=fields)

    with StringIO() as stream:
        printer.print(data, stream)
        printed_table = stream.getvalue()

    # Missing fields are printed as "None"
    # fmt: off
    assert printed_table == (
        "A    | B   \n"
        "---- | ----\n"
        "1    | None\n"
        "None | 5   \n"
    )
    # fmt: on


def test_data_table_raises_index_error_when_out_of_bounds_access():
    fields = (Field("A", "a"), Field("B", "b"))
    data = ({"a": 1, "b": 2}, {"a": 3, "b": 4})
    table = DataTable.from_data(fields=fields, data=data)

    with pytest.raises(IndexError, match="Table column index out of range"):
        table[2, 0]

    with pytest.raises(IndexError, match="Table row index out of range"):
        table[0, 2]
