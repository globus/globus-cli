from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk

from globus_cli.commands.gcs.endpoint.role._common import role_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import TextMode, display
from globus_cli.utils import resolve_principal_urn

_VALID_ROLES = ["administrator", "activity_manager", "activity_monitor"]


@command(
    "show",
)
@endpoint_id_arg
@click.argument("ROLE", type=click.Choice(_VALID_ROLES), metavar="ROLE")
@click.argument("PRINCIPAL", type=str)
@click.option(
    "--principal-type",
    type=click.Choice(["identity", "group"]),
    help="Qualifier to specify what type of principal (identity or group) is provided.",
)
@LoginManager.requires_login("transfer")
def create_command(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    role: t.Literal["administrator", "activity_manager", "activity_monitor"],
    principal: str,
    principal_type: t.Literal["identity", "group"] | None,
) -> None:
    """
    Create a role on a GCS Endpoint.

    ROLE may be one of: ["administrator", "activity_manager", "activity_monitor"].

    PRINCIPAL may be either a username or a UUID/URN for an identity or group.

       * If a UUID, you must also provide --principal-type.
    """
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    auth_client = login_manager.get_auth_client()

    # Format the principal into a URN
    principal_urn = resolve_principal_urn(
        auth_client=auth_client,
        principal_type=principal_type,
        principal=principal,
    )

    res = gcs_client.create_role(
        globus_sdk.GCSRoleDocument(role=role, principal=principal_urn)
    )

    display(res, text_mode=TextMode.text_record, fields=role_fields(auth_client))
