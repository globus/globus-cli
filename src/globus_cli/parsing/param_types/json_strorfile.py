from __future__ import annotations

import dataclasses
import json
import os
import sys
import typing as t

import click

from globus_cli.constants import EXPLICIT_NULL, ExplicitNullType
from globus_cli.types import JsonValue

from .annotated_param import AnnotatedParamType


@dataclasses.dataclass
class ParsedJSONData:
    # str means it's the path to a file input
    # including `-` for stdin
    # None means the parse came from an argument input
    filename: t.Union[str, None]
    # data is the parsed data
    data: JsonValue


class JSONStringOrFile(AnnotatedParamType):
    """
    Parse an input which could be a filename or could be a JSON blob being
    supplied on the commandline.

    For example,
        --opt './foo/bar.json'
        --opt "$(./myscript.sh)"

    For compatibility with the older mode of use, this param also supports a
    `file:` prefix which disambiguates an input as being a filename. e.g.
        --opt 'file:./foo/bar.json'

    The parsing happens in the following order of precedence:
        - 'file:' prefix (filename)
        - bare filename, including `-` for stdin
        - JSON parse

    This ordering protects against odd behavior if a filename happens to be valid JSON.
    Most likely to happen with a JSON literal like an integer, e.g. `--opt 100`

    The output of the parse is a loaded JSON object wrapped in a dataclass which
    contains contextual information. This can be useful for providing better error
    messages.
    """

    def __init__(
        self, *args: t.Any, null: t.Any | None = None, **kwargs: t.Any
    ) -> None:
        self.null = null
        super().__init__(*args, **kwargs)

    def get_metavar(self, param: click.Parameter) -> str:
        return "[JSON_FILE|JSON|file:JSON_FILE]"

    def get_type_annotation(self, param: click.Parameter) -> type:
        if self.null is not None:
            return t.cast(type, t.Union[ParsedJSONData, ExplicitNullType])
        else:
            return ParsedJSONData

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> ExplicitNullType | ParsedJSONData:
        if self.null is not None and value == self.null:
            return EXPLICIT_NULL

        if value.startswith("file:"):
            return self._do_file_parse(value[len("file:") :])
        elif os.path.exists(value) or value == "-":
            return self._do_file_parse(value)
        else:
            return self._do_json_parse(value)

    def _do_file_parse(self, value: str) -> ParsedJSONData:
        if value == "-":
            try:
                return ParsedJSONData(filename=value, data=json.load(sys.stdin))
            except json.JSONDecodeError:
                raise click.UsageError("stdin did not contain valid JSON")

        try:
            with open(value) as fp:
                return ParsedJSONData(filename=value, data=json.load(fp))
        except json.JSONDecodeError:
            raise click.UsageError(f"{value} did not contain valid JSON")
        except FileNotFoundError:
            raise click.UsageError(f"FileNotFound: {value} does not exist")

    def _do_json_parse(self, value: str) -> ParsedJSONData:
        try:
            return ParsedJSONData(filename=None, data=json.loads(value))
        except json.JSONDecodeError:
            # apply a *very weak* heuristic to try to get users accurate error
            # messages when they make typos
            #
            # if the value looks like it's meant to be JSON, show an invalid JSON error
            # but otherwise, it's a file-not-found error
            if value.startswith("{"):
                raise click.UsageError("parameter value did not contain valid JSON")
            raise click.UsageError(f"FileNotFound: {value} does not exist")
