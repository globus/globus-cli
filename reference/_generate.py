#!/usr/bin/env python3
"""asciidoc generator for CLI web pages

based originally on click-man, but significantly specialized for the globus-cli
"""
import os
import textwrap
import time

import click
import requests
from pkg_resources import load_entry_point

from globus_cli.utils import walk_contexts

CLI = load_entry_point("globus-cli", "console_scripts", "globus")
TARGET_DIR = os.path.dirname(__file__)

try:
    # try to fetch last release date
    last_release = requests.get(
        "https://api.github.com/repos/globus/globus-cli/releases/latest"
    )
    REV_DATE_T = time.strptime(
        last_release.json()["published_at"], "%Y-%m-%dT%H:%M:%SZ"
    )
except Exception:
    # fallback to current time
    REV_DATE_T = time.gmtime()
REV_DATE = time.strftime("%B %d, %Y", REV_DATE_T)

_EXIT_STATUS_TEXT_COMMON = """
2 if the command was used improperly.

3 if the command was used on the wrong type of object, e.g. a collection command used
on an endpoint.

4 if the command has authentication or authorization requirements which were not met,
as in ConsentRequired errors or missing logins.
"""

EXIT_STATUS_TEXT = (
    """0 on success.

1 if a network or server error occurred, unless --map-http-status has been
used to change exit behavior on http error codes.
"""
    + _EXIT_STATUS_TEXT_COMMON
)
EXIT_STATUS_NOHTTP_TEXT = (
    """0 on success.

1 if an error occurred.
"""
    + _EXIT_STATUS_TEXT_COMMON
)


def iter_all_commands(tree=None):
    ctx, subcmds, subgroups = tree or walk_contexts("globus", CLI)
    yield from subcmds
    for g in subgroups:
        yield from iter_all_commands(g)


def _format_option(optstr):
    opt = optstr.split()
    optnames, optparams = [], []
    for o in opt:
        if not optparams:
            # options like '--foo / --bar' or '--foo, --bar'
            if o.startswith("-") or o == "/":
                optnames.append(o)
                continue
        optparams.append(o)
    optnames = "*" + " ".join(optnames) + "*"
    optparams = " ".join([f"`{x}`" for x in optparams])
    return f"{optnames}{' ' if optparams else ''}{optparams}::\n"


class AdocPage:
    def __init__(self, ctx):
        self.commandname = ctx.command_path
        self.short_help = ctx.command.get_short_help_str()
        self.description = textwrap.dedent(ctx.command.help).replace("\b\n", "")
        self.synopsis = ctx.command.adoc_synopsis or self._format_synopsis(ctx)
        self.options = "\n\n".join(
            _format_option(y[0]) + "\n" + y[1].replace("\n\n", "\n+\n")
            for y in [
                x.get_help_record(ctx)
                for x in ctx.command.params
                if isinstance(x, click.Option)
            ]
            if y
        )
        self.output = ctx.command.adoc_output
        self.examples = ctx.command.adoc_examples
        uses_http = "map_http_status" not in ctx.command.globus_disable_opts
        self.exit_status_text = ctx.command.adoc_exit_status or (
            EXIT_STATUS_TEXT if uses_http else EXIT_STATUS_NOHTTP_TEXT
        )

    def _format_synopsis(self, ctx):
        usage_pieces = ctx.command.collect_usage_pieces(ctx)
        as_str = " ".join(usage_pieces)
        if as_str.endswith("..."):
            as_str = as_str[:-3]
        return f"`{self.commandname} {as_str}`"

    def __str__(self):
        sections = []
        sections.append(f"= {self.commandname.upper()}\n")
        sections.append(f"== NAME\n\n{self.commandname} - {self.short_help}\n")
        sections.append(f"== SYNOPSIS\n\n{self.synopsis}\n")
        if self.description:
            sections.append(f"== DESCRIPTION\n\n{self.description}\n")
        if self.options:
            sections.append(f"== OPTIONS\n{self.options}\n")
        if self.output:
            sections.append(f"== OUTPUT\n\n{self.output}\n")
        if self.examples:
            sections.append(f"== EXAMPLES\n\n{self.examples}\n")
        sections.append(f"== EXIT STATUS\n\n{self.exit_status_text}\n")
        return "\n".join(sections)


def write_pages():
    for ctx in iter_all_commands():
        if not isinstance(ctx.command, click.Group) and not getattr(
            ctx.command, "adoc_skip", True
        ):
            cmd_name = ctx.command_path.replace(" ", "_")[len("globus_") :]
            path = os.path.join(TARGET_DIR, cmd_name + ".adoc")
            with open(path, "w") as f:
                f.write(str(AdocPage(ctx)))


def commands_with_headings(heading, tree=None):
    ctx, subcmds, subgroups = tree or walk_contexts("globus", CLI)
    if subcmds:
        yield heading, subcmds
    for subgrouptree in subgroups:
        heading = f"== {subgrouptree[0].command_path} commands"
        yield from commands_with_headings(heading, subgrouptree)


def generate_index():
    with open(os.path.join(TARGET_DIR, "index.adoc"), "w") as f:
        # header required for globus docs to specify extra attributes
        f.write("---\nmenu_weight: 10\nshort_title: Reference\n---\n")
        for heading, commands in commands_with_headings(
            f"""= Command Line Interface (CLI) Reference

[doc-info]*Last Updated: {REV_DATE}*"""
        ):
            f.write(heading + "\n\n")
            for ctx in commands:
                link = ctx.command_path.replace(" ", "_")[len("globus_") :]
                f.write(f"link:{link}[{ctx.command_path}]::\n")
                f.write(ctx.command.get_short_help_str() + "\n\n")


if __name__ == "__main__":
    write_pages()
    generate_index()
