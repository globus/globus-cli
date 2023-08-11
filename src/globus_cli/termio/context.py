from __future__ import annotations

import os
import sys
import typing as t

import click

from globus_cli import utils
from globus_cli.parsing.command_state import CommandState


def outformat_is_json() -> bool:
    """
    Only safe to call within a click context.
    """
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    return state.outformat_is_json()


def outformat_is_unix() -> bool:
    """
    Only safe to call within a click context.
    """
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    return state.outformat_is_unix()


def outformat_is_text() -> bool:
    """
    Only safe to call within a click context.
    """
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    return state.outformat_is_text()


def get_jmespath_expression() -> t.Any:
    """
    Only safe to call within a click context.
    """
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    return state.jmespath_expr


def verbosity() -> int:
    """
    Only safe to call within a click context.
    """
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    return state.verbosity


def is_verbose() -> bool:
    """
    Only safe to call within a click context.
    """
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    return state.is_verbose()


def should_show_server_timing() -> bool:
    """
    Only safe to call within a click context.
    """
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    return state.show_server_timing


def out_is_terminal() -> bool:
    return sys.stdout.isatty()


def err_is_terminal() -> bool:
    return sys.stderr.isatty()


def env_interactive(raising: bool = False) -> bool | None:
    """
    Check the `GLOBUS_CLI_INTERACTIVE` environment variable for a boolean.
    """
    explicit_val = os.getenv("GLOBUS_CLI_INTERACTIVE")
    if explicit_val is None:
        return None
    result = utils.str2bool(explicit_val)
    if raising and result is None:
        click.echo(
            "Couldn't parse GLOBUS_CLI_INTERACTIVE environment variable. "
            f"Invalid truth value: '{explicit_val}'",
            err=True,
        )
        click.get_current_context().exit(1)
    return result


def term_is_interactive() -> bool:
    env = env_interactive()
    if env is not None:
        return env
    return os.getenv("PS1") is not None
