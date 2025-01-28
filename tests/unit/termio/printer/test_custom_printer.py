from globus_cli.termio.printers import CustomPrinter


def test_custom_printer_does_whatever_it_wants():
    called = False

    def custom_print(data):
        nonlocal called
        called = True

    printer = CustomPrinter(custom_print)
    printer.echo({"data": "data"})

    assert called
