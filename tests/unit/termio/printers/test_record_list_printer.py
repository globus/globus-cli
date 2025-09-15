from io import StringIO

from globus_cli.termio import Field
from globus_cli.termio.printers import RecordListPrinter


def test_record_list_printer_prints():
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

    printer = RecordListPrinter(fields=fields, max_content_width=80)

    with StringIO() as stream:
        printer.echo(data, stream)
        printed_records = stream.getvalue()

    assert printed_records == (
        "Column A: 1\n"
        "Column B: 4\n"
        "Column C: 7\n"
        "\n"
        "Column A: 2\n"
        "Column B: 5\n"
        "Column C: 8\n"
        "\n"
        "Column A: 3\n"
        "Column B: 6\n"
        "Column C: 9\n"
    )


def test_record_list_printer_wraps_long_values():
    fields = (
        Field("Column A", "a"),
        Field("Column B", "b", wrap_enabled=True),
    )
    data = (
        {"a": 1, "b": "b" * 10},
        {"a": 2, "b": "b"},
    )

    printer = RecordListPrinter(fields=fields, max_content_width=15)

    with StringIO() as stream:
        printer.echo(data, stream)
        printed_records = stream.getvalue()

    assert printed_records == (
        "Column A: 1\n"
        "Column B: bbbbb\n"
        "          bbbbb\n"
        "\n"
        "Column A: 2\n"
        "Column B: b\n"
    )
