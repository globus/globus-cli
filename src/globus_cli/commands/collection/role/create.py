import typing as t
import uuid

import click
import globus_sdk

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
    collection_id: uuid.UUID,
    role: str,
    principal: str,
    principal_type: t.Literal["identity", "group"] | None,
) -> None:
    """
    Create a role assignment on a Collection.

    ROLE must be one of:

    "administrator",
    "access_manager",
    "activity_manager",
    "activity_monitor"

    PRINCIPAL must be a username, UUID, or URN associated with a globus identity or
    group.

    If UUID, use `--principal-type` to specify the type (defaults to "identity").
    """

    gcs_client = login_manager.get_gcs_client(collection_id=collection_id)
    auth_client = login_manager.get_auth_client()

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

    display(res, simple_text="ID: {}".format(res["id"]))
