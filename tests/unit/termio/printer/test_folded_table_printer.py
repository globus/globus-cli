from io import StringIO

import pytest

from globus_cli.termio import Field
from globus_cli.termio.printers import FoldedTablePrinter
from globus_cli.termio.printers.folded_table_printer import Row, RowTable


@pytest.mark.parametrize(
    "init_setting, detection_result, expect_result",
    (
        pytest.param(True, False, True, id="override-true"),
        pytest.param(False, True, False, id="override-false"),
        pytest.param(None, True, True, id="detect-true"),
        pytest.param(None, False, False, id="detect-true"),
    ),
)
def test_folded_table_behavioral_flag_is_externally_controllable(
    init_setting, detection_result, expect_result, monkeypatch
):
    monkeypatch.setattr(
        "globus_cli.termio.printers.folded_table_printer._detect_folding_enabled",
        lambda: detection_result,
    )
    fields = (
        Field("Column A", "a"),
        Field("Column B", "b"),
    )

    printer = FoldedTablePrinter(fields=fields, folding_enabled=init_setting)
    assert printer._folding_enabled == expect_result


@pytest.mark.parametrize(
    "folding_enabled, width",
    (
        (False, 10),
        (False, 1000),
        (True, 1000),
    ),
)
def test_folded_table_printer_can_print_unfolded_output(folding_enabled, width):
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
    printer = FoldedTablePrinter(fields=fields, width=width)
    # override detection, set by test
    printer._folding_enabled = folding_enabled

    with StringIO() as stream:
        printer.echo(data, stream)
        printed_table = stream.getvalue()

    # fmt: off
    assert printed_table == (
        "Column A | Column B | Column C\n"
        "---------+----------+---------\n"
        "1        | 4        | 7       \n"
        "2        | 5        | 8       \n"
        "3        | 6        | 9       \n"
    )
    # fmt: on


def test_folded_table_printer_can_fold_in_half():
    fields = (
        Field("Column A", "a"),
        Field("Column B", "b"),
        Field("Column C", "c"),
        Field("Column D", "d"),
    )
    data = (
        {"a": 1, "b": 4, "c": 7, "d": "alpha"},
        {"a": 2, "b": 5, "c": 8, "d": "beta"},
        {"a": 3, "b": 6, "c": 9, "d": "gamma"},
    )

    printer = FoldedTablePrinter(fields=fields, width=25)
    # override detection of an interactive session
    printer._folding_enabled = True

    with StringIO() as stream:
        printer.echo(data, stream)
        printed_table = stream.getvalue()

    # fmt: off
    assert printed_table == (
        "╒══════════╤══════════╕\n"
        "│ Column A ╎ Column C │\n"
        "├─ ─ ─ ─  ─┼─ ─ ─ ─  ─┤\n"
        "│ Column B ╎ Column D │\n"
        "╞══════════╪══════════╡\n"
        "│ 1        ╎ 7        │\n"
        "├─ ─ ─ ─  ─┼─ ─ ─ ─  ─┤\n"
        "│ 4        ╎ alpha    │\n"
        "├──────────┼──────────┤\n"
        "│ 2        ╎ 8        │\n"
        "├─ ─ ─ ─  ─┼─ ─ ─ ─  ─┤\n"
        "│ 5        ╎ beta     │\n"
        "├──────────┼──────────┤\n"
        "│ 3        ╎ 9        │\n"
        "├─ ─ ─ ─  ─┼─ ─ ─ ─  ─┤\n"
        "│ 6        ╎ gamma    │\n"
        "└──────────┴──────────┘\n"
    )
    # fmt: on


def test_folded_table_printer_can_fold_in_half_unevenly():
    fields = (
        Field("Column A", "a"),
        Field("Column B", "b"),
        Field("Column C", "c"),
    )
    data = (
        {"a": 1, "b": 4, "c": 7, "d": "alpha"},
        {"a": 2, "b": 5, "c": 8, "d": "beta"},
        {"a": 3, "b": 6, "c": 9, "d": "gamma"},
    )

    printer = FoldedTablePrinter(fields=fields, width=25)
    # override detection of an interactive session
    printer._folding_enabled = True

    with StringIO() as stream:
        printer.echo(data, stream)
        printed_table = stream.getvalue()

    # fmt: off
    assert printed_table == (
        "╒══════════╤══════════╕\n"
        "│ Column A ╎ Column C │\n"
        "├─ ─ ─ ─  ─┼─ ─ ─ ─  ─┤\n"
        "│ Column B ╎          │\n"
        "╞══════════╪══════════╡\n"
        "│ 1        ╎ 7        │\n"
        "├─ ─ ─ ─  ─┼─ ─ ─ ─  ─┤\n"
        "│ 4        ╎          │\n"
        "├──────────┼──────────┤\n"
        "│ 2        ╎ 8        │\n"
        "├─ ─ ─ ─  ─┼─ ─ ─ ─  ─┤\n"
        "│ 5        ╎          │\n"
        "├──────────┼──────────┤\n"
        "│ 3        ╎ 9        │\n"
        "├─ ─ ─ ─  ─┼─ ─ ─ ─  ─┤\n"
        "│ 6        ╎          │\n"
        "└──────────┴──────────┘\n"
    )
    # fmt: on


def test_row_folding_no_remainder():
    six_items = Row((("1", "2", "3", "4", "5", "6"),))

    # fold by 2 or "in half"
    fold2 = six_items.fold(2)
    assert len(fold2.grid) == 2
    assert fold2.grid == (
        ("1", "3", "5"),  # odds
        ("2", "4", "6"),  # evens
    )

    # fold by 3 or "in thirds"
    fold3 = six_items.fold(3)
    assert len(fold3.grid) == 3
    assert fold3.grid == (
        ("1", "4"),
        ("2", "5"),
        ("3", "6"),
    )

    # fold by N where N is the number of columns
    fold6 = six_items.fold(6)
    assert len(fold6.grid) == 6
    assert fold6.grid == (
        ("1",),
        ("2",),
        ("3",),
        ("4",),
        ("5",),
        ("6",),
    )


def test_row_folding_with_remainder():
    five_items = Row(
        (
            (
                "1",
                "2",
                "3",
                "4",
                "5",
            ),
        )
    )

    # fold by 2 or "in half"
    fold2 = five_items.fold(2)
    assert len(fold2.grid) == 2
    assert fold2.grid == (
        ("1", "3", "5"),  # odds
        (
            "2",
            "4",
        ),  # evens
    )

    # fold by 3 or "in thirds"
    fold3 = five_items.fold(3)
    assert len(fold3.grid) == 3
    assert fold3.grid == (
        ("1", "4"),
        ("2", "5"),
        ("3",),
    )


def test_row_table_width_computation_is_pessimal():
    """
    Given a table with lopsided rows, such that each row could fit in a narrow width,
    but when column-aligned they are wider, the table should find the width based on
    the justification of text.
    """
    row1 = Row((("a" * 1000, "b"),))
    row2 = Row((("c", "d" * 1000),))

    table = RowTable((row1, row2))

    # it should be the max width for each column (1000) + the width of separators (in
    # this case, 3 for the center divider)
    assert table.calculate_width() == 2003


@pytest.mark.parametrize("folding_enabled", (False, True))
def test_folded_table_printer_bolds_headers(monkeypatch, folding_enabled):
    fields = (
        Field("Column A", "a"),
        Field("Column B", "b"),
        Field("Column C", "c"),
    )
    data = ({"a": 1, "b": 2, "c": 3},)
    printer = FoldedTablePrinter(fields=fields, width=1000)
    # override detection, set by test
    printer._folding_enabled = folding_enabled

    capture = []

    def echo_capture(s, file=None):
        capture.append(s)

    monkeypatch.setattr("click.echo", echo_capture)
    printer.echo(data, None)

    start_bold = "\N{ESCAPE}[1m"
    end_bold = "\N{ESCAPE}[0m"

    assert capture == [
        (
            f"{start_bold}Column A{end_bold} | "
            f"{start_bold}Column B{end_bold} | "
            f"{start_bold}Column C{end_bold}"
        ),
        # point of comparison for alignment:
        # Column A | Column B | Column C
        "---------+----------+---------",
        "1        | 2        | 3       ",
    ]
