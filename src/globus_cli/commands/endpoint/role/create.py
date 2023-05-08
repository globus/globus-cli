from __future__ import annotations

import sys
import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg, security_principal_opts
from globus_cli.termio import display

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


@command(
    "create",
    short_help="Add a role to an endpoint",
    adoc_output=(
        "Textual output is a simple success message in the absence of errors, "
        "containing the ID of the created role."
    ),
    adoc_examples="""Grant 'demo@globus.org' the 'activity_monitor' role on
'ddb59aef-6d04-11e5-ba46-22000b92c6ec':

[source,bash]
----
$ globus endpoint role create 'ddb59aef-6d04-11e5-ba46-22000b92c6ec' \
    --identity 'demo@globus.org' --role activity_monitor
----
""",
)
@endpoint_id_arg
@security_principal_opts(allow_provision=True)
@click.option(
    "--role",
    required=True,
    type=click.Choice(
        ("administrator", "access_manager", "activity_manager", "activity_monitor"),
        case_sensitive=False,
    ),
    help="A role to assign.",
)
@LoginManager.requires_login("auth", "transfer")
def role_create(
    *,
    login_manager: LoginManager,
    role: Literal[
        "administrator", "access_manager", "activity_manager", "activity_monitor"
    ],
    principal: tuple[str, str],
    endpoint_id: uuid.UUID,
) -> None:
    """
    Create a role on an endpoint.
    You must have sufficient privileges to modify the roles on the endpoint.

    Either *--group* or *--identity* is required. You may not pass both.
    Which one of these options you use will determine the 'Principal Type' on the
    role, and the value given will be the 'Principal' of the resulting role.
    The term "Principal" is used in the sense of "a security principal", an entity
    which has some privileges associated with it.
    """
    from globus_cli.services.transfer import assemble_generic_doc

    principal_type, principal_val = principal

    transfer_client = login_manager.get_transfer_client()
    auth_client = login_manager.get_auth_client()

    if principal_type == "identity":
        principal_val = auth_client.maybe_lookup_identity_id(principal_val)
        if not principal_val:
            raise click.UsageError(
                "Identity does not exist. "
                "Use --provision-identity to auto-provision an identity."
            )
    elif principal_type == "provision-identity":
        principal_val = auth_client.maybe_lookup_identity_id(
            principal_val, provision=True
        )
        principal_type = "identity"

    role_doc = assemble_generic_doc(
        "role", principal_type=principal_type, principal=principal_val, role=role
    )

    res = transfer_client.add_endpoint_role(endpoint_id, role_doc)
    display(res, simple_text="ID: {}".format(res["id"]))
