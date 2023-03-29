"""
This module defines all of the tools needed to decorate commands and groups.
All customizations that apply specifically to the main command go here as well.

Ultimately, `globus_cli.parsing` will export only the decorators defined here,
and all other components will be hidden internals.
"""
from __future__ import annotations

import importlib
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
        self.adoc_output = kwargs.pop("adoc_output", None)
        self.adoc_examples = kwargs.pop("adoc_examples", None)
        self.globus_disable_opts = kwargs.pop("globus_disable_opts", [])
        self.adoc_exit_status = kwargs.pop("adoc_exit_status", None)
        self.adoc_synopsis = kwargs.pop("adoc_synopsis", None)
        self.opts_to_combine = kwargs.pop("opts_to_combine", {})

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
            # if we have any opts to be combined in order, do that now
            if self.opts_to_combine:
                combined_opts: dict[str, list[tuple[str, str]]] = {
                    combined_name: [] for combined_name in self.opts_to_combine.values()
                }
                parser = self.make_parser(ctx)
                values, _, order = parser.parse_args(args=list(args))
                # values is a dict of value lists keyed by their option name
                # in order for that value and order is a list of option names
                # in the order they were given at the command line
                # we want a list of (name, value) tuples for multiple options
                # in the order they were given at the command line
                for opt in order:
                    if opt.name and opt.name in self.opts_to_combine:
                        value = values[opt.name].pop(0)
                        combined_name = self.opts_to_combine[opt.name]
                        combined_opts[combined_name].append((opt.name, value))

                ctx.params.update(combined_opts)

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

    def __init__(
        self,
        *args,
        lazy_subcommands: dict[str, tuple[str, str]] | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        # lazy_subcommands is a map of the form:
        #
        #   {command-name} -> ({module-name}, {command-object-name})
        #
        self.lazy_subcommands: dict[str, tuple[str, str]] = lazy_subcommands or {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        base = super().list_commands(ctx)
        lazy = sorted(self.lazy_subcommands.keys())
        return base + lazy

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        if cmd_name in self.lazy_subcommands:
            return self._lazy_load(ctx, cmd_name)
        return super().get_command(ctx, cmd_name)

    def _lazy_load(self, ctx: click.Context, cmd_name: str) -> click.Command:
        # lazily loading a command, first get the module name and attribute name
        modname, cmd_object_name = self.lazy_subcommands[cmd_name]
        # if the module name is relative (leading dot), resolve it relative to the
        # callback function's module, so that we get the location where this was
        # *probably* defined
        if modname.startswith("."):
            full_modname = self.callback.__module__ + modname
            mod = importlib.import_module(modname, self.callback.__module__)
        # otherwise, resolve it relative to the commands subpackage
        else:
            full_modname = "globus_cli.commands." + modname
            mod = importlib.import_module("." + modname, "globus_cli.commands")
        cmd_object = getattr(mod, cmd_object_name)
        if not isinstance(cmd_object, click.Command):
            raise ValueError(
                f"Lazy loading of {full_modname}.{cmd_object_name} failed by returning "
                "a non-command object"
            )
        return cmd_object

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


def main_group(**kwargs):
    def decorator(f):
        f = click.group("globus", cls=TopLevelGroup, **kwargs)(f)
        f = common_options(f)
        f = print_completer_option(f)
        return f

    return decorator


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
