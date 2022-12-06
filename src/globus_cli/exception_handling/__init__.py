"""
Setup a custom except hook which formats exceptions that are uncaught.
In "DEBUGMODE", we'll just use the typical sys.excepthook behavior and print a
stacktrace. It's really for debugging problems with the CLI itself, but it
might also come in handy if we have issues with the way that we're trying to
format an exception.
Define an except hook per exception type that we want to treat specially,
generally types of SDK errors, and dispatch onto tht set of hooks.
"""
from __future__ import annotations

import sys
import types
import typing as t

import click
import click.exceptions

from globus_cli.parsing.command_state import CommandState

from .hooks import register_all_hooks
from .registry import find_handler

register_all_hooks()


def custom_except_hook(
    exc_info: tuple[type[Exception], Exception, types.TracebackType]
) -> t.NoReturn:
    """
    A custom excepthook to present python errors produced by the CLI.
    We don't want to show end users big scary stacktraces if they aren't python
    programmers, so slim it down to some basic info. We keep a "DEBUGMODE" env
    variable kicking around to let us turn on stacktraces if we ever need them.
    """
    exception_type, exception, traceback = exc_info

    # check if we're in debug mode, and run the real excepthook if we are
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    if state.debug:
        sys.excepthook(exception_type, exception, traceback)

    # we're not in debug mode, do custom handling

    # look for a relevant registered handler
    handler = find_handler(exception)
    if handler:
        handler(exception)

    # if it's a click exception, re-raise as original -- Click's main
    # execution context will handle pretty-printing
    if isinstance(
        exception, (click.ClickException, click.exceptions.Abort, click.exceptions.Exit)
    ):
        raise exception.with_traceback(traceback)

    # not a GlobusError, not a ClickException -- something like ValueError
    # or NotImplementedError bubbled all the way up here: just print it out
    click.echo(
        "{}: {}".format(
            click.style(exception_type.__name__, bold=True, fg="red"), exception
        ),
        err=True,
    )
    click.get_current_context().exit(1)
