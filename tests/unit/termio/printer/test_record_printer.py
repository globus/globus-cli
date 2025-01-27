from io import StringIO

import pytest

from globus_cli.termio import Field
from globus_cli.termio.printers import RecordPrinter


def test_record_printer_prints():
    fields = (
        Field("Column A", "a"),
        Field("Column B", "b"),
        Field("Column C", "c"),
    )
    data = {"a": 1, "b": 4, "c": 7}

    printer = RecordPrinter(fields=fields, max_width=80)

    with StringIO() as stream:
        printer.print(data, stream)
        printed_record = stream.getvalue()

    # fmt: off
    assert printed_record == (
        "Column A: 1\n"
        "Column B: 4\n"
        "Column C: 7\n"
    )
    # fmt: on


def test_record_printer_wraps_long_values():
    fields = (
        Field("Column A", "a"),
        Field("Column B", "b", wrap_enabled=True),
        Field("Column C", "c"),
    )
    data = {"a": 1, "b": "a" * 40, "c": 7}

    printer = RecordPrinter(fields=fields, max_width=25)

    with StringIO() as stream:
        printer.print(data, stream)
        printed_record = stream.getvalue()

    # fmt: off
    assert printed_record == (
        "Column A: 1\n"
        f"Column B: {'a' * 15}\n"
        f"          {'a' * 15}\n"
        f"          {'a' * 10}\n"
        "Column C: 7\n"
    )
    # fmt: on


def test_record_printer_respects_field_wrap_setting():
    fields = (
        Field("Wrapped", "a", wrap_enabled=True),
        Field("Not Wrapped", "b", wrap_enabled=False),
    )
    data = {"a": "a" * 10, "b": "b" * 10}

    printer = RecordPrinter(fields=fields, max_width=20)

    with StringIO() as stream:
        printer.print(data, stream)
        printed_record = stream.getvalue()

    # fmt: off
    assert printed_record == (
        "Wrapped:     aaaaaaa\n"
        "             aaa\n"
        "Not Wrapped: bbbbbbbbbb\n"
    )
    # fmt: on


def test_record_printer_maintains_data_newlines_when_wrapping():
    fields = (Field("Wrapped", "a", wrap_enabled=True),)
    data = {"a": "a\nbcdefghij"}

    printer = RecordPrinter(fields=fields, max_width=15)

    with StringIO() as stream:
        printer.print(data, stream)
        printed_record = stream.getvalue()

    # fmt: off
    assert printed_record == (
        "Wrapped: a\n"
        "         bcdefg\n"
        "         hij\n"
    )
    # fmt: on


def test_record_printer_matches_longest_key_length():
    fields = (
        Field("Column A", "a"),
        Field("Really Long Column B", "b"),
        Field("C", "c"),
    )
    data = {"a": 1, "b": 4, "c": 7}

    printer = RecordPrinter(fields=fields, max_width=80)

    with StringIO() as stream:
        printer.print(data, stream)
        printed_record = stream.getvalue()

    # fmt: off
    assert printed_record == (
        "Column A:             1\n"
        "Really Long Column B: 4\n"
        "C:                    7\n"
    )
    # fmt: on


def test_record_printer_ignores_extra_fields():
    fields = (Field("A", "a"), Field("B", "b"))
    data = {"a": 1, "b": 2, "c": 3}

    printer = RecordPrinter(fields=fields)

    with StringIO() as stream:
        printer.print(data, stream)
        printed_record = stream.getvalue()

    # fmt: off
    assert printed_record == (
        "A: 1\n"
        "B: 2\n"
    )
    # fmt: on


def test_record_printer_handles_missing_fields():
    fields = (Field("Column A", "a"), Field("Column B", "b"))
    data = {"a": 1}

    printer = RecordPrinter(fields=fields)

    with StringIO() as stream:
        printer.print(data, stream)
        printed_record = stream.getvalue()

    # fmt: off
    assert printed_record == (
        "Column A: 1\n"
        "Column B: None\n"
    )
    # fmt: on


@pytest.mark.parametrize(
    "columns,max_width",
    (
        (80, 80),
        # If the terminal width is > 100, we only use 80% of it.
        (120, 96),
    ),
)
def test_record_printer_sets_default_width(monkeypatch, columns, max_width):
    monkeypatch.setenv("COLUMNS", str(columns))

    printer = RecordPrinter(fields=(Field("A", "a"),))
    assert printer._item_wrapper.width == max_width
