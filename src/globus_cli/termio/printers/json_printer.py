from __future__ import annotations

import json
import typing as t

import click
import globus_sdk

from globus_cli.types import JsonValue

from .base import Printer

DataObject = t.Union[JsonValue, globus_sdk.GlobusHTTPResponse]


class JsonPrinter(Printer[DataObject]):
    """
    A printer to render a json data object in a pretty-printed format:

    {
      "a": "b",
      "c": [
        "d",
        "e"
      ],
      "f": 7
    }

    :param sort_keys: if True, sort the keys of the json object before printing.
    """

    def __init__(self, *, sort_keys: bool = True) -> None:
        self._sort_keys = sort_keys

    def print(self, data: DataObject, stream: t.IO[str] | None = None) -> None:
        res = JsonPrinter.jmespath_preprocess(data)
        res = json.dumps(res, indent=2, sort_keys=self._sort_keys)
        click.echo(res, file=stream)
