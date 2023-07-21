from __future__ import annotations

import sys
import typing as t
import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import AnnotatedParamType, command, endpoint_id_arg
from globus_cli.termio import Field, TextMode, display, formatters

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class ChoiceSlugified(click.Choice, AnnotatedParamType):
    """
    Allow either hyphens or underscores, e.g. both 'mapped-collections' or
    'mapped_collections'
    """

    def get_type_annotation(self, param: click.Parameter) -> type:
        return t.cast(type, Literal[tuple(self._slugify(c) for c in self.choices)])

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> t.Any:
        if value is None:
            return None
        return self._slugify(super().convert(value.replace("_", "-"), param, ctx))

    def _slugify(self, value: str) -> str:
        return value.replace("-", "_")


@command("list", short_help="List all Collections on an Endpoint")
@endpoint_id_arg
@click.option(
    "--filter",
    "filters",
    multiple=True,
    # choices are shown with hyphens, but the command will receive them with underscores
    type=ChoiceSlugified(
        ["mapped-collections", "guest-collections", "managed-by-me", "created-by-me"],
        case_sensitive=False,
    ),
    help="""\
Filter results to one of the specified categories of collections. Can be applied
multiple times. Note that mutually exclusive filters are allowed and will find no
results.

The filters are as follows

\b
mapped-collections:
  Only show collections with collection_type="mapped"

\b
guest-collections:
  Only show collections with collection_type="guest"

\b
managed-by-me:
  Only show collections where one of your identities has a role

\b
created-by-me:
  Only show collections where one of your identities was the creator
""",
)
@click.option(
    "--include-private-policies",
    is_flag=True,
    help=(
        "Include private policies. Requires administrator role on the endpoint. Some "
        "policy data may only be visible in `--format JSON` output"
    ),
)
@click.option(
    "--mapped-collection-id",
    default=None,
    type=click.UUID,
    help=(
        "Filter results to Guest Collections on a specific Mapped Collection. This is "
        "the ID of the Mapped Collection"
    ),
)
@LoginManager.requires_login("auth", "transfer")
def collection_list(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    include_private_policies: bool,
    filters: tuple[
        Literal[
            "mapped_collections", "guest_collections", "managed_by_me", "created_by_me"
        ],
        ...,
    ],
    mapped_collection_id: uuid.UUID | None,
) -> None:
    """
    List the Collections on a given Globus Connect Server v5 Endpoint
    """
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    auth_client = login_manager.get_auth_client()
    params: dict[str, t.Any] = {}
    if mapped_collection_id:
        params["mapped_collection_id"] = mapped_collection_id
    # note `filter` (no s) is the argument to `get_collection_list`
    if filters:
        params["filter"] = ",".join(filters)
    if include_private_policies:
        params["include"] = "private_policies"
    res = gcs_client.get_collection_list(**params)
    display(
        res,
        text_mode=TextMode.text_table,
        fields=[
            Field("ID", "id"),
            Field("Display Name", "display_name"),
            Field(
                "Owner",
                "identity_id",
                formatter=formatters.auth.IdentityIDFormatter(auth_client),
            ),
            Field("Collection Type", "collection_type"),
            Field("Storage Gateway ID", "storage_gateway_id"),
        ],
    )
