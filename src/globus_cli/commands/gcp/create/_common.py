import typing as t

import click

from globus_cli import utils
from globus_cli.parsing import MutexInfo, mutex_option_group
from globus_cli.termio import print_command_hint

F = t.TypeVar("F", bound=t.Union[click.BaseCommand, t.Callable])


def deprecated_verify_option(f: F) -> F:
    return utils.fold_decorators(
        f,
        [
            click.option(
                "--disable-verify/--no-disable-verify",
                hidden=True,
                is_flag=True,
                default=None,
                callback=_warning_callback,
            ),
            mutex_option_group(
                MutexInfo("--disable-verify", present=lambda val: val is not None),
                "--verify",
            ),
        ],
    )


def _warning_callback(
    ctx: click.Context, param: click.Parameter, value: t.Any
) -> t.Any:
    if value is not None:
        print_command_hint(
            """\
'--disable-verify/--no-disable-verify' is deprecated

Use the '--verify' option instead."""
        )
    return value
