from __future__ import annotations

import typing as t

import click
import globus_sdk

from globus_cli.termio import Field, field_formatters


def index_id_arg(f: t.Callable) -> t.Callable:
    return click.argument("index_id", metavar="INDEX_ID", type=click.UUID)(f)


def task_id_arg(f: t.Callable) -> t.Callable:
    return click.argument("task_id", metavar="TASK_ID", type=click.UUID)(f)


class _PrincipalFormatter(field_formatters.FieldFormatter[t.Tuple[str, str, str]]):
    def __init__(
        self,
        auth_client: globus_sdk.AuthClient,
        *,
        type_key: str = "principal_type",
        value_key: str = "principal",
    ) -> None:
        self.type_key = type_key
        self.value_key = value_key
        self.resolved_ids = globus_sdk.IdentityMap(auth_client)

    def add_items(self, items: t.Iterable[dict]) -> None:
        for x in items:
            if x.get(self.type_key) != "identity":
                continue
            self.resolved_ids.add(t.cast(str, x[self.value_key]).split(":")[-1])

    def parse(self, value: t.Any) -> tuple[str, str, str]:
        if not isinstance(value, dict):
            raise ValueError("cannot format principal from non-dict data")

        unparsed_principal = t.cast(str, value[self.value_key])

        return (
            value[self.type_key],
            unparsed_principal.split(":")[-1],
            unparsed_principal,
        )

    def render(self, value: tuple[str, str, str]) -> str:
        ptype, pvalue, unparsed = value
        if ptype == "identity":
            try:
                return t.cast(str, self.resolved_ids[pvalue]["username"])
            except LookupError:
                return pvalue
        elif ptype == "group":
            return f"Globus Group ({pvalue})"
        else:
            return unparsed


def resolved_principals_field(
    auth_client: globus_sdk.AuthClient,
    items: t.Iterable[dict[str, t.Any]] | None = None,
) -> Field:
    formatter = _PrincipalFormatter(auth_client)
    if items is not None:
        formatter.add_items(items)

    return Field("Principal", "@", formatter=formatter)


INDEX_FIELDS = [
    Field("Index ID", "id"),
    Field("Display Name", "display_name"),
    Field("Status", "status"),
]
