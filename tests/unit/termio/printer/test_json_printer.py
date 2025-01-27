from io import StringIO

import click

from globus_cli.termio.printers import JsonPrinter


def test_json_printer_prints_with_sorted_keys():
    printer = JsonPrinter()
    data = {"b": 1, "a": 2, "c": 3}

    with StringIO() as stream:
        with click_context():
            printer.print(data, stream)
            printed_json = stream.getvalue()

    # fmt: off
    assert printed_json == (
        "{\n"
        '  "a": 2,\n'
        '  "b": 1,\n'
        '  "c": 3\n'
        "}\n"
    )
    # fmt: on


def test_json_printer_prints_without_sorted_keys():
    printer = JsonPrinter(sort_keys=False)
    data = {"b": 1, "a": 2, "c": 3}

    with StringIO() as stream:
        with click_context():
            printer.print(data, stream)
            printed_json = stream.getvalue()

    # fmt: off
    assert printed_json == (
        "{\n"
        '  "b": 1,\n'
        '  "a": 2,\n'
        '  "c": 3\n'
        "}\n"
    )
    # fmt: on


def click_context(command: str = "cmd") -> click.Context:
    ctx = click.Context(click.Command(command), obj={"jmespath": "a.b."})
    return ctx
