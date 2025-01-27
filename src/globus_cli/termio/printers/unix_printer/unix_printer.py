from __future__ import annotations

import typing as t

import click
import globus_sdk

from globus_cli.types import JsonValue

from ..base import Printer
from .awscli_text import unix_display

DataObject = t.Union[JsonValue, globus_sdk.GlobusHTTPResponse]


class UnixPrinter(Printer[DataObject]):
    """
    Printer to render data objects in a format suitable for consumption by UNIX tools.

    This is a thin wrapper around the AWS CLI's text formatter, which is a simple
    key-value pair format with no headers or footers.
    """

    def print(self, data: DataObject, stream: t.IO[str] | None = None) -> None:
        res = UnixPrinter.jmespath_preprocess(data)

        try:
            unix_display(res, stream=stream)  # type: ignore[no-untyped-call]
        # Attr errors indicate that we got data which cannot be unix formatted
        # likely a scalar + non-scalar in an array, though there may be other cases
        # print good error and exit(2) (Count this as UsageError!)
        except AttributeError:
            click.echo(
                "UNIX formatting of output failed."
                "\n  "
                "This usually means that data has a structure which cannot be "
                "handled by the UNIX formatter."
                "\n  "
                "To avoid this error in the future, ensure that you query the "
                'exact properties you want from output data with "--jmespath"',
                err=True,
            )
            click.get_current_context().exit(2)
        pass
