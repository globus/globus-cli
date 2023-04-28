"""
Tools for self-inspection or "reflection" of the CLI.
Used for autodocumentation and testing.

By keeping the tools as part of the application, we make them testable under the
standard testsuite.
"""
from __future__ import annotations

import typing as t

import click

from globus_cli.commands import main as main_entrypoint
from globus_cli.types import ClickContextTree


def load_main_entrypoint() -> click.MultiCommand:
    return t.cast(click.MultiCommand, main_entrypoint)


def walk_contexts(
    name: str,
    cmd: click.MultiCommand,
    parent_ctx: click.Context | None = None,
    skip_hidden: bool = True,
) -> ClickContextTree:
    """
    A recursive walk over click Contexts for all commands in a tree
    Returns the results in a tree-like structure as triples,
      (context, subcommands, subgroups)

    subcommands is a list of contexts
    subgroups is a list of (context, subcommands, subgroups) triples
    """
    current_ctx = click.Context(cmd, info_name=name, parent=parent_ctx)
    cmds, groups = [], []
    for subcmdname in cmd.list_commands(current_ctx):
        subcmd = cmd.get_command(current_ctx, subcmdname)
        # it should be impossible, but if there is no such command, skip
        if subcmd is None:
            continue
        # explicitly skip hidden commands
        if subcmd.hidden and skip_hidden:
            continue

        if not isinstance(subcmd, click.Group):
            cmds.append(click.Context(subcmd, info_name=subcmdname, parent=current_ctx))
        else:
            groups.append(
                walk_contexts(subcmdname, subcmd, current_ctx, skip_hidden=skip_hidden)
            )

    return (current_ctx, cmds, groups)


def iter_all_commands(
    *,
    cli_main: click.MultiCommand | None = None,
    tree: ClickContextTree | None = None,
    skip_hidden: bool = True,
) -> t.Iterator[click.Context]:
    """
    A recursive walk over all commands, done by walking all contexts in the tree and
    yielding back only the contexts themselves.
    """
    if cli_main is None:
        cli_main = load_main_entrypoint()

    ctx, subcmds, subgroups = tree or walk_contexts(
        "globus", cli_main, skip_hidden=skip_hidden
    )
    yield from subcmds
    for g in subgroups:
        yield from iter_all_commands(cli_main=cli_main, tree=g, skip_hidden=skip_hidden)
