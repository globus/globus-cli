"""
This module defines all of the tools needed to decorate commands and groups.
All customizations that apply specifically to the main command go here as well.

Ultimately, `globus_cli.parsing` will export only the decorators defined here,
and all other components will be hidden internals.
"""
from __future__ import annotations

import logging
import sys
from shutil import get_terminal_size

import click

from globus_cli.exception_handling import custom_except_hook
from globus_cli.termio import env_interactive

from .shared_options import common_options
from .shell_completion import print_completer_option

log = logging.getLogger(__name__)


class GlobusCommand(click.Command):
    """
    A custom command class which stores the special attributes
    of the form "adoc_*" with defaults of None. This lets us pass additional info to the
    adoc generator.

    It also automatically runs string formatting on command helptext to allow the
    inclusion of common strings (e.g. autoactivation help).
    """

    AUTOMATIC_ACTIVATION_HELPTEXT = """=== Automatic Endpoint Activation

    This command requires all endpoints it uses to be activated. It will attempt to
    auto-activate any endpoints that are not active, but if auto-activation fails,
    you will need to manually activate the endpoint. See 'globus endpoint activate'
    for more details."""

    def __init__(self, *args, **kwargs):
        self.adoc_skip = kwargs.pop("adoc_skip", False)
        self.adoc_output = kwargs.pop("adoc_output", None)
        self.adoc_examples = kwargs.pop("adoc_examples", None)
        self.globus_disable_opts = kwargs.pop("globus_disable_opts", [])
        self.adoc_exit_status = kwargs.pop("adoc_exit_status", None)
        self.adoc_synopsis = kwargs.pop("adoc_synopsis", None)

        helptext = kwargs.pop("help", None)
        if helptext:
            kwargs["help"] = helptext.format(
                AUTOMATIC_ACTIVATION=self.AUTOMATIC_ACTIVATION_HELPTEXT
            )
        if "context_settings" not in kwargs:
            kwargs["context_settings"] = {}
        if "max_content_width" not in kwargs["context_settings"]:
            try:
                cols = get_terminal_size(fallback=(80, 20)).columns
                content_width = cols if cols < 100 else int(0.8 * cols)
                kwargs["context_settings"]["max_content_width"] = content_width
            except OSError:
                pass
        super().__init__(*args, **kwargs)

    def invoke(self, ctx):
        log.debug("command invoke start")
        try:
            return super().invoke(ctx)
        finally:
            log.debug("command invoke exit")

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        # args will be consumed, so check it before super()
        had_args = bool(args)
        try:
            return super().parse_args(ctx, args)
        except click.MissingParameter as e:
            if not had_args:
                click.secho(e.format_message(), fg="yellow", err=True)
                click.echo("\n" + ctx.get_help(), err=True)
                ctx.exit(2)
            raise


class GlobusCommandEnvChecks(GlobusCommand):
    def invoke(self, ctx):
        try:
            env_interactive()
        except ValueError as e:
            click.echo(
                f"couldn't parse GLOBUS_CLI_INTERACTIVE environment variable: {e}",
                err=True,
            )
            click.get_current_context().exit(1)
        return super().invoke(ctx)


class GlobusCommandGroup(click.Group):
    """
    This is a click.Group with any customizations which we deem necessary
    *everywhere*.

    In particular, at present it provides a better form of handling for
    no_args_is_help. If that flag is set, helptext will be triggered not only
    off of cases where there are no arguments at all, but also cases where
    there are options, but no subcommand (positional arg) is given.
    """

    def invoke(self, ctx):
        # if no subcommand was given (but, potentially, flags were passed),
        # ctx.protected_args will be empty
        # improves upon the built-in detection given on click.Group by
        # no_args_is_help , since that treats options (without a subcommand) as
        # being arguments and blows up with a "Missing command" failure
        # for reference to the original version (as of 2017-02-26):
        # https://github.com/pallets/click/blob/02ea9ee7e864581258b4902d6e6c1264b0226b9f/click/core.py#L1039-L1052
        if self.no_args_is_help and not ctx.protected_args:
            click.echo(ctx.get_help())
            ctx.exit()
        return super().invoke(ctx)


class TopLevelGroup(GlobusCommandGroup):
    """
    This is a custom command type which is basically a click.Group, but is
    designed specifically for the top level command.
    It's specialization is that it catches all exceptions from subcommands and
    passes them to a custom error handler.
    """

    def invoke(self, ctx):
        try:
            return super().invoke(ctx)
        except Exception:
            custom_except_hook(sys.exc_info())


def main_group(f):
    f = click.group("globus", cls=TopLevelGroup)(f)
    f = common_options(f)
    f = print_completer_option(f)
    return f


def command(*args, **kwargs):
    """
    A helper for decorating commands a-la `click.command`, but pulling the help string
    from `<function>.__doc__` by default.

    Also allows the use of custom arguments, which are stored on the command, as in
    "adoc_examples".

    `skip_env_checks` is used to disable environment variable validation prior to
    running a command, but is ignored when a specific `cls` argument is passed.
    """
    disable_opts = kwargs.pop("disable_options", [])

    def _inner_decorator(func):
        if "cls" not in kwargs:
            if kwargs.get("skip_env_checks", False) is True:
                kwargs["cls"] = GlobusCommand
            else:
                kwargs["cls"] = GlobusCommandEnvChecks

        kwargs["globus_disable_opts"] = disable_opts

        return common_options(disable_options=disable_opts)(
            click.command(*args, **kwargs)(func)
        )

    return _inner_decorator


def group(*args, **kwargs):
    """
    Wrapper over click.group which sets GlobusCommandGroup as the Class

    Caution!
    Don't get snake-bitten by this. `group` is a decorator which MUST
    take arguments. It is not wrapped in our common detect-and-decorate pattern
    to allow it to be used bare -- that wouldn't work (unnamed groups? weird
    stuff)
    """
    disable_opts = kwargs.pop("disable_options", [])

    def inner_decorator(f):
        f = click.group(*args, cls=GlobusCommandGroup, **kwargs)(f)
        f = common_options(disable_options=disable_opts)(f)
        return f

    return inner_decorator
