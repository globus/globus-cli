from __future__ import annotations

import typing as t

from globus_cli.termio.printers import Printer


class CustomPrinter(Printer[t.Any]):
    """
    A printer that uses a custom print function to print data.
    """

    def __init__(self, custom_print: t.Callable[[t.Any], None]) -> None:
        self._custom_print = custom_print

    def echo(self, data: t.Any, stream: t.IO[str] | None = None) -> None:
        self._custom_print(data)
