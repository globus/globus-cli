from __future__ import annotations

from typing import Any, Callable, Iterable

import click
import globus_sdk

from globus_cli.types import FIELD_LIST_T


def index_id_arg(f: Callable) -> Callable:
    return click.argument("index_id", metavar="INDEX_ID", type=click.UUID)(f)


def task_id_arg(f: Callable) -> Callable:
    return click.argument("task_id", metavar="TASK_ID", type=click.UUID)(f)


def resolved_principals_field(
    auth_client: globus_sdk.AuthClient,
    items: Iterable[dict[str, Any]] | None = None,
    *,
    name: str = "Principal",
    type_key: str = "principal_type",
    value_key: str = "principal",
) -> tuple[str, Callable[[dict], str]]:
    resolved_ids = globus_sdk.IdentityMap(
        auth_client,
        (x[value_key].split(":")[-1] for x in items if x[type_key] == "identity")
        if items
        else [],
    )

    def render_principal(item: dict[str, Any]) -> str:
        value = item[value_key].split(":")[-1]
        if item[type_key] == "identity":
            try:
                ret = resolved_ids[value]["username"]
            except LookupError:
                ret = value
        elif item[type_key] == "group":
            ret = f"Globus Group ({value})"
        else:
            ret = item[value_key]
        return str(ret)

    return (name, render_principal)


INDEX_FIELDS: FIELD_LIST_T = [
    ("Index ID", "id"),
    ("Display Name", "display_name"),
    ("Status", "status"),
]
