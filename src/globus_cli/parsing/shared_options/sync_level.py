from __future__ import annotations

import functools
from typing import Callable, TypeVar, Union, cast, overload

import click

C = TypeVar("C", bound=Union[Callable, click.Command])


@overload
def sync_level_option(f: C) -> C:
    ...


@overload
def sync_level_option(f: C, *, aliases: tuple[str, ...]) -> C:
    ...


@overload
def sync_level_option() -> Callable[[C], C]:
    ...


@overload
def sync_level_option(*, aliases: tuple[str, ...]) -> Callable[[C], C]:
    ...


def sync_level_option(
    f: C | None = None, *, aliases: tuple[str, ...] = ()
) -> Callable[[C], C] | C:
    if f is None:
        return cast(
            Callable[[C], C], functools.partial(sync_level_option, aliases=aliases)
        )
    return click.option(
        "--sync-level",
        *aliases,
        default=None,
        show_default=True,
        type=click.Choice(
            ("exists", "size", "mtime", "checksum"), case_sensitive=False
        ),
        help=(
            "Specify that only new or modified files should be transferred, depending "
            "on which setting is provided"
        ),
    )(f)
