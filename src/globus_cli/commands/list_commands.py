from __future__ import annotations

import typing as t

import click

from globus_cli.parsing import command
from globus_cli.reflect import walk_contexts
from globus_cli.types import ClickContextTree


def _print_command(cmd_ctx: click.Context) -> None:
    # print commands with short_help
    short_help = cmd_ctx.command.get_short_help_str()
    name = cmd_ctx.command_path

    click.echo(f"    {name}")
    click.echo(f"        {short_help}\n")


def _print_tree(
    ctx: click.Context,
    subcommands: list[click.Context],
    subgroups: list[ClickContextTree],
) -> None:
    click.echo(f"\n=== {ctx.command_path} ===\n")
    for cmd_ctx in subcommands:
        _print_command(cmd_ctx)
    for subctx, subsubcommands, subsubgroups in subgroups:
        _print_tree(subctx, subsubcommands, subsubgroups)


@command(
    "list-commands",
    short_help="List all CLI Commands.",
    help=(
        "List all Globus CLI Commands with short help output. "
        "For full command help, run the command with the "
        "`--help` flag"
    ),
)
def list_commands() -> None:
    """
    Prints the name and a short description of every command available in the globus
    cli. Commands are grouped by their parent commands.
    """
    # get the root context (the click context for the entire CLI tree)
    root_ctx = click.get_current_context().find_root()
    ctx, subcmds, subgroups = walk_contexts(
        "globus", t.cast(click.MultiCommand, root_ctx.command)
    )
    _print_tree(ctx, subcmds, subgroups)
    # get an extra newline at the end
    click.echo("")
