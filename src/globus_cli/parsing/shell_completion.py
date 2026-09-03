from __future__ import annotations

import os
import typing as t

import click
from click.shell_completion import (
    BashComplete,
    FishComplete,
    ShellComplete,
    ZshComplete,
)

C = t.TypeVar("C", bound=t.Union[t.Callable[..., t.Any], click.Command])


def print_completer_option(f: C) -> C:
    def callback(ctx: click.Context, param: click.Parameter, value: str | None) -> None:
        # if `resilient_parsing=True`, shell completion is being executed, so we should
        # be careful to skip the callback contents, which would echo output and exit
        if not value or ctx.resilient_parsing:
            return

        if value == "BASH":
            cls: type[ShellComplete] = BashComplete
        elif value == "FISH":
            cls = FishComplete
        elif value == "ZSH":
            cls = ZshComplete
        else:  # auto
            cls = BashComplete  # Default to bash completion.
            if "SHELL" in os.environ:
                if os.environ["SHELL"].endswith("zsh"):
                    cls = ZshComplete

        root_ctx = ctx.find_root()
        completer = cls(
            cli=root_ctx.command,
            ctx_args={},
            prog_name="globus",
            complete_var="_GLOBUS_COMPLETE",
        )
        click.echo(completer.source())
        ctx.exit(0)

    def _compopt(flag: str, value: str) -> t.Callable[[C], C]:
        return click.option(
            flag,
            hidden=True,
            is_eager=True,
            expose_value=False,
            flag_value=value,
            callback=callback,
        )

    f = _compopt("--completer", "auto")(f)
    f = _compopt("--bash-completer", "BASH")(f)
    f = _compopt("--fish-completer", "FISH")(f)
    f = _compopt("--zsh-completer", "ZSH")(f)
    return f
