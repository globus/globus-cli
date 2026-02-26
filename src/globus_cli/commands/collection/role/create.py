from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk

from globus_cli.commands.collection.role._fields import collection_role_format_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import collection_id_arg, command
from globus_cli.termio import display
from globus_cli.utils import resolve_principal_urn

_VALID_ROLES = t.Literal[
    "access_manager", "activity_manager", "activity_monitor", "administrator"
]


@command("create")
@collection_id_arg
@click.argument("ROLE", type=click.Choice(t.get_args(_VALID_ROLES)), metavar="ROLE")
@click.argument("PRINCIPAL", type=str, required=False)
@click.option(
    "--principal-type",
    type=click.Choice(["identity", "group"]),
    help="Qualifier to specify what type of principal (identity or group) is provided.",
)
@LoginManager.requires_login("transfer")
def create_command(
    login_manager: LoginManager,
    *,
    collection_id: uuid.UUID,
    role: t.Literal[
        "access_manager", "activity_manager", "activity_monitor", "administrator"
    ],
    principal: str | None,
    principal_type: t.Literal["identity", "group"] | None,
) -> None:
    """
    Create a role assignment on a Collection.

    ROLE must be one of:

    "administrator",
    "access_manager",
    "activity_manager",
    "activity_monitor"

    If a PRINCIPAL value is not provided the primary identity of the logged in user will
    be used.

    If a PRINCIPAL value is provided, it must be a username, UUID, or URN associated
    with a globus identity or group.

    If UUID, use `--principal-type` to specify the type (defaults to "identity").
    """

    gcs_client = login_manager.get_gcs_client(collection_id=collection_id)
    auth_client = login_manager.get_auth_client()

    # If Principal argument isn't provided, determine user's primary identity
    if principal is None:
        userinfo = auth_client.userinfo()
        principal = userinfo["sub"]

    # Format the principal into a URN
    principal_urn = resolve_principal_urn(
        auth_client=auth_client,
        principal_type=principal_type,
        principal=principal,
    )

    res = gcs_client.create_role(
        globus_sdk.GCSRoleDocument(
            DATA_TYPE="role#1.0.0",
            collection=collection_id,
            role=role,
            principal=principal_urn,
        )
    )

    fields = collection_role_format_fields(auth_client, res.data)

    display(res, text_mode=display.RECORD, fields=fields)
