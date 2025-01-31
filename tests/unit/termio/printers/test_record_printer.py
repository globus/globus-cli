from io import StringIO

from globus_cli.termio import Field
from globus_cli.termio.printers import RecordPrinter
from globus_cli.termio.terminal_info import TERM_INFO


def test_record_printer_prints():
    fields = (
        Field("Column A", "a"),
        Field("Column B", "b"),
        Field("Column C", "c"),
    )
    data = {"a": 1, "b": 4, "c": 7}

    printer = RecordPrinter(fields=fields, content_width=80)

    with StringIO() as stream:
        printer.echo(data, stream)
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

    printer = RecordPrinter(fields=fields, content_width=25)

    with StringIO() as stream:
        printer.echo(data, stream)
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

    printer = RecordPrinter(fields=fields, content_width=20)

    with StringIO() as stream:
        printer.echo(data, stream)
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

    printer = RecordPrinter(fields=fields, content_width=15)

    with StringIO() as stream:
        printer.echo(data, stream)
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

    printer = RecordPrinter(fields=fields, content_width=80)

    with StringIO() as stream:
        printer.echo(data, stream)
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
        printer.echo(data, stream)
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
        printer.echo(data, stream)
        printed_record = stream.getvalue()

    # fmt: off
    assert printed_record == (
        "Column A: 1\n"
        "Column B: None\n"
    )
    # fmt: on


def test_record_printer_sets_default_content_width():
    expected_content_width = TERM_INFO.columns
    printer = RecordPrinter(fields=(Field("A", "a"),))
    assert printer._item_wrapper.width == expected_content_width


def test_record_printer_respects_explicit_content_width():
    printer = RecordPrinter(fields=(Field("A", "a"),), content_width=5000)
    assert TERM_INFO.columns != 5000
    assert printer._item_wrapper.width == 5000
