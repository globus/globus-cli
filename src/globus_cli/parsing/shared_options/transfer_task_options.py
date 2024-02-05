from __future__ import annotations

import textwrap
import typing as t

import click

C = t.TypeVar("C", bound=t.Union[t.Callable, click.Command])


def sync_level_option(*, aliases: tuple[str, ...] = ()) -> t.Callable[[C], C]:
    def decorator(f: C) -> C:
        return click.option(
            "--sync-level",
            *aliases,
            default=None,
            show_default=True,
            type=click.Choice(
                ("exists", "size", "mtime", "checksum"), case_sensitive=False
            ),
            help=(
                "Specify that only new or modified files should be transferred, "
                "depending on which setting is provided."
            ),
        )(f)

    return decorator


def transfer_recursive_option(f: C) -> C:
    return click.option(
        "--recursive/--no-recursive",
        "-r",
        is_flag=True,
        default=None,
        help=(
            "Use --recursive to flag that the paths are directories "
            "and should be transferred recursively. "
            "Use --no-recursive to flag that the paths are files "
            "that must not be transferred recursively. "
            "Omit these options to use path type auto-detection."
        ),
    )(f)


def transfer_batch_option(f: C) -> C:
    return click.option(
        "--batch",
        type=click.File("r"),
        help=textwrap.dedent(
            """\
            Accept a batch of source/dest path pairs from a file.
            Use `-` to read from stdin.

            Uses SOURCE_ENDPOINT_ID and DEST_ENDPOINT_ID as passed on the
            commandline.

            See documentation on "Batch Input" for more information.
            """
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
            "Skip over source paths that hit permission denied, file not "
            "found, or ambiguous path errors during the transfer."
        ),
    )(f)


def preserve_timestamp_option(*, aliases: tuple[str, ...] = ()) -> t.Callable[[C], C]:
    def decorator(f: C) -> C:
        return click.option(
            "--preserve-timestamp",
            *aliases,
            is_flag=True,
            default=False,
            help=(
                "Preserve file modification times. "
                "Directory modification times are not preserved."
            ),
        )(f)

    return decorator


def verify_checksum_option(f: C) -> C:
    return click.option(
        "--verify-checksum/--no-verify-checksum",
        default=True,
        show_default=True,
        help="Verify checksum after transfer.",
    )(f)


def encrypt_data_option(*, aliases: tuple[str, ...] = ()) -> t.Callable[[C], C]:
    def decorator(f: C) -> C:
        return click.option(
            "--encrypt-data",
            *aliases,
            is_flag=True,
            default=False,
            help="Encrypt data sent through the network.",
        )(f)

    return decorator
