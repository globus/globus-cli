from __future__ import annotations

import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import Field, TextMode, display

from ._common import RolePrincipalFormatter, role_id_arg


@command(
    "show",
    short_help="Show full info for a role on an endpoint",
    adoc_output="""Textual output has the following fields:

- 'Principal Type'
- 'Principal'
- 'Role'

The principal is a user or group ID, and the principal type says which of these
types the principal is. The term "Principal" is used in the sense of "a
security principal", an entity which has some privileges associated with it.
""",
    adoc_examples="""Show detail for a specific role on an endpoint

[source,bash]
----
$ globus endpoint role show EP_ID ROLE_ID
----
""",
)
@endpoint_id_arg
@role_id_arg
@LoginManager.requires_login("auth", "transfer")
def role_show(
    *, login_manager: LoginManager, endpoint_id: uuid.UUID, role_id: str
) -> None:
    """
    Show full info for a role on an endpoint.

    This does not show information about the permissions granted by a role; only what
    role a user or group has been granted, by name.

    You must have sufficient privileges to see the roles on the endpoint.
    """
    transfer_client = login_manager.get_transfer_client()
    auth_client = login_manager.get_auth_client()
    formatter = RolePrincipalFormatter(auth_client)

    role = transfer_client.get_endpoint_role(endpoint_id, role_id)
    display(
        role,
        text_mode=TextMode.text_record,
        fields=[
            Field("Principal Type", "principal_type"),
            Field("Principal", "@", formatter=formatter),
            Field("Role", "role"),
        ],
    )
