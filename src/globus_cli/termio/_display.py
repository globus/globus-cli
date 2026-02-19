from __future__ import annotations

import enum
import typing as t

import click
import globus_sdk

from .context import (
    outformat_is_json,
    outformat_is_record,
    outformat_is_table,
    outformat_is_text,
    outformat_is_unix,
)
from .field import Field
from .printers import (
    CustomPrinter,
    JsonPrinter,
    Printer,
    RecordListPrinter,
    RecordPrinter,
    TablePrinter,
    UnixPrinter,
)
from .server_timing import maybe_show_server_timing


class TextMode(enum.Enum):
    silent = enum.auto()
    json = enum.auto()
    text_table = enum.auto()
    text_record = enum.auto()
    text_record_list = enum.auto()
    text_raw = enum.auto()
    text_custom = enum.auto()


class Renderer:
    """
    A primary interface for rendering output in various formats.
    Since this is the primary interface for rendering output, it is exposed as a
    singleton callable: ``display()``.

    See the ``__call__`` method for parameter documentation.
    """

    TABLE = TextMode.text_table
    SILENT = TextMode.silent
    JSON = TextMode.json
    RECORD = TextMode.text_record
    RECORD_LIST = TextMode.text_record_list
    RAW = TextMode.text_raw

    def __call__(
        self,
        response_data: t.Any,
        *,
        stream: t.IO[str] | None = None,
        simple_text: str | None = None,
        text_preamble: str | None = None,
        text_epilog: str | None = None,
        text_mode: TextMode | t.Callable[[t.Any], None] = TextMode.text_table,
        fields: list[Field] | None = None,
        response_key: str | t.Callable[[t.Any], t.Any] | None = None,
        json_converter: t.Callable[..., t.Any] | None = None,
        sort_json_keys: bool = True,
    ) -> None:
        """
        Format and print data.

        :param response_data: The data to print. Data type will differ depending on
        text mode; but generally this will be a single data object (JSON Element |
        GlobusHTTPResponse) or a sequence of data objects.

        :param stream: An IO stream to write to. Default: stdout.

        :param simple_text: A string override; if given this string is printed instead
        of the normal output.
        :param text_preamble: A string to print before the normal output.
        :param text_epilog: A string to print after the normal output.

        :param text_mode: A field to flag how to render ``response_data``.
          - If a TextMode is given, an appropriate ``Printer`` is instantiated and
            used to render the data.
          - If a callable is given, it is used directly to render and print.

        :param fields: A list of Fields to be printed and their associated keys.
            Only keys with a corresponding field will be formatted & printed.
            (text output only)
        :param response_key: A mechanism to index deeper into a response object. Either:
            - A string key to index into a dict-like object.
            - A callable to perform custom indexing into any object.
            (text output only)

        :param json_converter: a callable to preprocess of JSON output. It must accept
            ``response_data`` and produce another dict or dict-like object
            (json/unix output only)
        :param sort_json_keys: If True, JSON keys are rendered sorted. Default: True.
            (json output only)
        """

        # if --format record was used, change table outputs into record_lists.
        # no-op if output format is already record or record list. error on
        # other output types.
        if outformat_is_record():
            if text_mode not in (
                TextMode.text_table,
                TextMode.text_record,
                TextMode.text_record_list,
            ):
                raise click.UsageError(
                    "This command does not support record output formatting"
                )
            if text_mode == TextMode.text_table:
                text_mode = TextMode.text_record_list

        # if --format table was used, change record list outputs into table
        # outputs. no-op if output format is already table. error on other
        # output types.
        elif outformat_is_table():
            if text_mode not in (TextMode.text_table, TextMode.text_record_list):
                raise click.UsageError(
                    "This command does not support table output formatting"
                )
            text_mode = TextMode.text_table

        if isinstance(response_data, globus_sdk.GlobusHTTPResponse):
            maybe_show_server_timing(response_data)

        if self._print_special_format(
            response_data,
            stream=stream,
            simple_text=simple_text,
            text_mode=text_mode,
            json_converter=json_converter,
            sort_json_keys=sort_json_keys,
        ):
            return

        data = self._index_response_data(response_data, response_key)
        printer = self._resolve_printer(text_mode, data, fields)

        if text_preamble is not None:
            click.echo(text_preamble, file=stream)

        printer.echo(data, stream=stream)

        if text_epilog is not None:
            click.echo(text_epilog, file=stream)

    def _print_special_format(
        self,
        response_data: t.Any,
        *,
        stream: t.IO[str] | None,
        simple_text: str | None = None,
        text_mode: TextMode | t.Callable[[t.Any], None],
        json_converter: t.Callable[..., t.Any] | None,
        sort_json_keys: bool,
    ) -> bool:
        """
        Handle special format cases which don't fit the typical rendering/printing flow.

        :returns: True if a special format was matched, False otherwise
        """
        if outformat_is_json() or (outformat_is_text() and text_mode == self.JSON):
            data = json_converter(response_data) if json_converter else response_data
            JsonPrinter(sort_keys=sort_json_keys).echo(data, stream=stream)
        elif outformat_is_unix():
            data = json_converter(response_data) if json_converter else response_data
            UnixPrinter().echo(data, stream=stream)
        elif simple_text is not None:
            click.echo(simple_text, file=stream)
        elif text_mode != self.SILENT:
            return False
        return True

    def _index_response_data(
        self,
        response_data: t.Any,
        response_key: str | t.Callable[[t.Any], t.Any] | None,
    ) -> t.Any:
        if response_key is None:
            return response_data
        if callable(response_key):
            return response_key(response_data)
        return response_data[response_key]

    def _resolve_printer(
        self,
        text_mode: TextMode | t.Callable[[t.Any], None],
        data: t.Any,
        fields: list[Field] | None,
    ) -> Printer[t.Any]:
        if not isinstance(text_mode, TextMode):
            return CustomPrinter(custom_print=text_mode)

        if text_mode in (self.TABLE, self.RECORD, self.RECORD_LIST):
            fields = _assert_fields(fields)
            if text_mode == self.RECORD:
                return RecordPrinter(fields)

            _assert_iterable(data)
            if text_mode == self.TABLE:
                return TablePrinter(fields)
            if text_mode == self.RECORD_LIST:
                return RecordListPrinter(fields)

        # Fallback to just printing the data raw.
        return CustomPrinter(custom_print=click.echo)


def _assert_fields(fields: list[Field] | None) -> list[Field]:
    if fields is not None:
        return fields
    raise ValueError(
        "Internal Error! Output format requires fields; none given. "
        "You can workaround this error by using `--format JSON`."
    )


def _assert_iterable(data: t.Any) -> None:
    if not hasattr(data, "__iter__"):
        raise ValueError(
            f"Internal Error! This output format requires a list but got a "
            f"{type(data)}. You can workaround this error by using `--format JSON`."
        )


display = Renderer()

__all__ = ("display",)
