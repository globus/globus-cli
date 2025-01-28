import click

from ._display import display
from .context import (
    env_interactive,
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
from .field import Field


def print_command_hint(message: str, *, color: str = "yellow") -> None:
    """
    Wrapper around echo that checks terminal state
    before printing a given command hint message
    """
    if term_is_interactive() and err_is_terminal() and out_is_terminal():
        click.echo(click.style(message, fg=color), err=True)


__all__ = [
    "print_command_hint",
    "PrintableErrorField",
    "write_error_info",
    "Field",
    "display",
    "out_is_terminal",
    "env_interactive",
    "err_is_terminal",
    "term_is_interactive",
    "outformat_is_json",
    "outformat_is_text",
    "outformat_is_unix",
    "get_jmespath_expression",
    "verbosity",
    "is_verbose",
]
