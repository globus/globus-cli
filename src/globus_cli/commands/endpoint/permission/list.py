from __future__ import annotations

import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import Field, display

from ._common import AclPrincipalFormatter


@command(
    "list",
    short_help="List access control rules.",
    adoc_examples="""[source,bash]
----
$ ep_id=aa752cea-8222-5bc8-acd9-555b090c0ccb
$ globus endpoint permission list $ep_id
----
""",
)
@endpoint_id_arg
@LoginManager.requires_login("auth", "transfer")
def list_command(login_manager: LoginManager, *, endpoint_id: uuid.UUID) -> None:
    """List all rules in an endpoint's access control list."""
    transfer_client = login_manager.get_transfer_client()
    auth_client = login_manager.get_auth_client()

    rules = transfer_client.endpoint_acl_list(endpoint_id)

    formatter = AclPrincipalFormatter(auth_client)
    formatter.add_items(*rules)

    display(
        rules,
        fields=[
            Field("Rule ID", "id"),
            Field("Permissions", "permissions"),
            Field("Shared With", "@", formatter=formatter),
            Field("Path", "path"),
        ],
    )
