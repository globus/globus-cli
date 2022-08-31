from __future__ import annotations

import functools
from typing import Callable, TypeVar, Union, cast, overload

import click

C = TypeVar("C", bound=Union[Callable, click.Command])


@overload
def sync_level_option(f: C) -> C:
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


def transfer_recursive_option(f: C) -> C:
    return click.option(
        "--recursive",
        "-r",
        is_flag=True,
        help="SOURCE_PATH and DEST_PATH are both directories, "
        "do a recursive directory transfer",
    )(f)


def transfer_batch_option(f: C) -> C:
    return click.option(
        "--batch",
        type=click.File("r"),
        help=(
            "Accept a batch of source/dest path pairs from a file. Use the special `-` "
            "value to read from stdin; otherwise opens the file from the argument and "
            "passes through lines from that file. Uses SOURCE_ENDPOINT_ID and "
            "DEST_ENDPOINT_ID as passed on the commandline. Commandline paths are "
            "still allowed and are used as prefixes to the batchmode inputs."
        ),
    )(f)


def fail_on_quota_errors_option(f: C) -> C:
    return click.option(
        "--fail-on-quota-errors",
        is_flag=True,
        default=False,
        show_default=True,
        help=(
            "Cause the task to fail if any quota exceeded errors are hit "
            "during the transfer."
        ),
    )(f)


def skip_source_errors_option(f: C) -> C:
    return click.option(
        "--skip-source-errors",
        is_flag=True,
        default=False,
        show_default=True,
        help=(
            "Skip over source paths that hit permission denied or file not "
            "found errors during the transfer."
        ),
    )(f)


@overload
def preserve_timestamp_option(f: C) -> C:
    ...


@overload
def preserve_timestamp_option(*, aliases: tuple[str, ...]) -> Callable[[C], C]:
    ...


def preserve_timestamp_option(
    f: C | None = None, *, aliases: tuple[str, ...] = ()
) -> Callable[[C], C] | C:
    if f is None:
        return cast(
            Callable[[C], C],
            functools.partial(preserve_timestamp_option, aliases=aliases),
        )
    return click.option(
        "--preserve-timestamp",
        *aliases,
        is_flag=True,
        default=False,
        help="Preserve file and directory modification times.",
    )(f)


def verify_checksum_option(f: C) -> C:
    return click.option(
        "--verify-checksum/--no-verify-checksum",
        default=True,
        show_default=True,
        help="Verify checksum after transfer.",
    )(f)


@overload
def encrypt_data_option(f: C) -> C:
    ...


@overload
def encrypt_data_option(*, aliases: tuple[str, ...]) -> Callable[[C], C]:
    ...


def encrypt_data_option(
    f: C | None = None, *, aliases: tuple[str, ...] = ()
) -> Callable[[C], C] | C:
    if f is None:
        return cast(
            Callable[[C], C],
            functools.partial(encrypt_data_option, aliases=aliases),
        )
    return click.option(
        "--encrypt-data",
        *aliases,
        is_flag=True,
        default=False,
        help="Encrypt data sent through the network.",
    )(f)
