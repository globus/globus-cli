import click

from .context import (
    err_is_terminal,
    get_jmespath_expression,
    is_verbose,
    out_is_terminal,
    outformat_is_json,
    outformat_is_text,
    outformat_is_unix,
    term_is_interactive,
    verbosity,
)
from .errors import PrintableErrorField, write_error_info
from .output_formatter import (
    FORMAT_JSON,
    FORMAT_SILENT,
    FORMAT_TEXT_RAW,
    FORMAT_TEXT_RECORD,
    FORMAT_TEXT_TABLE,
    FormatField,
    formatted_print,
)
from .shell_completion import print_completion as print_experimental_completion


def print_command_hint(message):
    """
    Wrapper around echo that checks terminal state
    before printing a given command hint message
    """
    if term_is_interactive() and err_is_terminal() and out_is_terminal():
        click.echo(click.style(message, fg="yellow"), err=True)


__all__ = [
    "print_command_hint",
    "PrintableErrorField",
    "write_error_info",
    "formatted_print",
    "FormatField",
    "FORMAT_SILENT",
    "FORMAT_JSON",
    "FORMAT_TEXT_TABLE",
    "FORMAT_TEXT_RECORD",
    "FORMAT_TEXT_RAW",
    "out_is_terminal",
    "err_is_terminal",
    "term_is_interactive",
    "outformat_is_json",
    "outformat_is_text",
    "outformat_is_unix",
    "get_jmespath_expression",
    "verbosity",
    "is_verbose",
    "print_experimental_completion",
]
