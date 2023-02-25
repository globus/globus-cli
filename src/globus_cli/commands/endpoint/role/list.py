import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import Field, display

from ._common import RolePrincipalFormatter


@command(
    "list",
    short_help="List roles on an endpoint",
    adoc_output="""Textual output has the following fields:

- 'Principal Type'
- 'Role ID'
- 'Principal'
- 'Role'

The principal is a user or group ID, and the principal type says which of these
types the principal is. The term "Principal" is used in the sense of "a
security principal", an entity which has some privileges associated with it.
""",
    adoc_examples="""Show all roles on 'ddb59aef-6d04-11e5-ba46-22000b92c6ec':

[source,bash]
----
$ globus endpoint role list 'ddb59aef-6d04-11e5-ba46-22000b92c6ec'
----
""",
)
@endpoint_id_arg
@LoginManager.requires_login("auth", "transfer")
def role_list(*, login_manager: LoginManager, endpoint_id: uuid.UUID) -> None:
    """
    List the assigned roles on an endpoint.

    You must have sufficient privileges to see the roles on the endpoint.
    """
    transfer_client = login_manager.get_transfer_client()
    roles = transfer_client.endpoint_role_list(endpoint_id)

    formatter = RolePrincipalFormatter(login_manager.get_auth_client())
    for r in roles:
        formatter.add_item(r)

    display(
        roles,
        fields=[
            Field("Principal Type", "principal_type"),
            Field("Role ID", "id"),
            Field("Principal", "@", formatter=formatter),
            Field("Role", "role"),
        ],
    )
