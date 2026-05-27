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
import typing as t
from shutil import get_terminal_size

import click

from globus_cli.exception_handling import custom_except_hook
from globus_cli.termio import env_interactive

from .shared_options import common_options
from .shell_completion import print_completer_option

C = t.TypeVar("C", bound=t.Union[click.Command, t.Callable[..., t.Any]])

log = logging.getLogger(__name__)


class GlobusCommand(click.Command):
    """
    A custom command class which stores the special attributes
    of the form "adoc_*" with defaults of None. This lets us pass additional info to the
    adoc generator.

    It also automatically runs string formatting on command helptext to allow the
    inclusion of common strings (e.g. autoactivation help) and handles
    custom argument parsing.

    opts_to_combine is an interface for combining multiple options while preserving
    their original order. Given a dict of original option names as keys
    and combined option names as values, options are combined into a list of
    tuples of the original option name and value. For example:

    @command(
        ...
        opts_to_combine={
            "foo": "foo_bar",
            "bar": "foo_bar",
        },
    @click.option("--foo", multiple=True, expose_value=False)
    @click.option("--bar", multiple=True, expose_value=False)
    def example_command(*, foo_bar: list[tuple[Literal["foo", "bar"], Any]]):

        for option in foo_bar:
            original_option_name, value = option

    """

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        self.adoc_output = kwargs.pop("adoc_output", None)
        self.adoc_examples = kwargs.pop("adoc_examples", None)
        self.globus_disable_opts = kwargs.pop("globus_disable_opts", [])
        self.adoc_exit_status = kwargs.pop("adoc_exit_status", None)
        self.adoc_synopsis = kwargs.pop("adoc_synopsis", None)
        self.opts_to_combine = kwargs.pop("opts_to_combine", {})

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

    def invoke(self, ctx: click.Context) -> t.Any:
        log.debug("command invoke start")
        try:
            # this isn't forcing interactive mode, it's just checking to see that
            # the GLOBUS_CLI_INTERACTIVE value is *valid*
            env_interactive(raising=True)
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
        *args: t.Any,
        lazy_subcommands: dict[str, tuple[str, str]] | None = None,
        **kwargs: t.Any,
    ) -> None:
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


class TopLevelGroup(GlobusCommandGroup):
    """
    This is a custom command type which is basically a click.Group, but is
    designed specifically for the top level command.
    It's specialization is that it catches all exceptions from subcommands and
    passes them to a custom error handler.
    """

    def invoke(self, ctx: click.Context) -> t.Any:
        try:
            return super().invoke(ctx)
        # explicitly re-raise any IOError (e.g. broken pipe) in order to engage
        # click's existing handling of broken pipes
        except OSError:
            raise
        except Exception:
            # mypy thinks that exc_info could be (None, None, None), but... nope. False.
            custom_except_hook(sys.exc_info())  # type: ignore[arg-type,type-var]


def main_group(**kwargs: t.Any) -> t.Callable[[C], TopLevelGroup]:
    def decorator(f: C) -> TopLevelGroup:
        grp = click.group("globus", cls=TopLevelGroup, **kwargs)(f)
        grp = common_options()(grp)
        grp = print_completer_option(grp)
        return grp

    return decorator


def command(*args: t.Any, **kwargs: t.Any) -> t.Callable[[C], GlobusCommand]:
    """
    A helper for decorating commands a-la `click.command`, but pulling the help string
    from `<function>.__doc__` by default.

    Also allows the use of custom arguments, which are stored on the command, as in
    "adoc_examples".
    """
    disable_opts = kwargs.pop("disable_options", [])

    def _inner_decorator(func: C) -> GlobusCommand:
        kwargs["globus_disable_opts"] = disable_opts

        return common_options(disable_options=disable_opts)(
            click.command(*args, cls=GlobusCommand, **kwargs)(func)
        )

    return _inner_decorator


def group(*args: t.Any, **kwargs: t.Any) -> t.Callable[[C], GlobusCommandGroup]:
    """
    Wrapper over click.group which sets GlobusCommandGroup as the Class

    Caution!
    Don't get snake-bitten by this. `group` is a decorator which MUST
    take arguments. It is not wrapped in our common detect-and-decorate pattern
    to allow it to be used bare -- that wouldn't work (unnamed groups? weird
    stuff)
    """
    disable_opts = kwargs.pop("disable_options", [])

    def inner_decorator(f: C) -> GlobusCommandGroup:
        grp = click.group(*args, cls=GlobusCommandGroup, **kwargs)(f)
        grp = common_options(disable_options=disable_opts)(grp)
        return grp

    return inner_decorator
