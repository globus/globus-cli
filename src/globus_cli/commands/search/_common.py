from __future__ import annotations

import typing as t

import click
import globus_sdk

from globus_cli.termio import Field, formatters
from globus_cli.types import AnyCommand

C = t.TypeVar("C", bound=AnyCommand)


def index_id_arg(f: C) -> C:
    return click.argument("index_id", metavar="INDEX_ID", type=click.UUID)(f)


def task_id_arg(f: C) -> C:
    return click.argument("task_id", metavar="TASK_ID", type=click.UUID)(f)


def resolved_principals_field(
    auth_client: globus_sdk.AuthClient,
    items: t.Iterable[dict[str, t.Any]] | None = None,
) -> Field:
    formatter = formatters.auth.PrincipalURNFormatter(auth_client)
    if items is not None:
        formatter.add_items(*items)

    return Field("Principal", "principal", formatter=formatter)


INDEX_FIELDS = [
    Field("Index ID", "id"),
    Field("Display Name", "display_name"),
    Field("Status", "status"),
]
