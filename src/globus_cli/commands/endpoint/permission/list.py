import uuid

import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import Field, formatted_print


@command(
    "list",
    short_help="List access control rules",
    adoc_examples="""[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint permission list $ep_id
----
""",
)
@endpoint_id_arg
@LoginManager.requires_login(LoginManager.AUTH_RS, LoginManager.TRANSFER_RS)
def list_command(*, login_manager: LoginManager, endpoint_id: uuid.UUID):
    """List all rules in an endpoint's access control list."""
    transfer_client = login_manager.get_transfer_client()
    auth_client = login_manager.get_auth_client()

    rules = transfer_client.endpoint_acl_list(endpoint_id)

    resolved_ids = globus_sdk.IdentityMap(
        auth_client,
        (x["principal"] for x in rules if x["principal_type"] == "identity"),
    )

    def principal_str(rule):
        principal = rule["principal"]
        if rule["principal_type"] == "identity":
            try:
                return resolved_ids[principal]["username"]
            except KeyError:
                return principal
        if rule["principal_type"] == "group":
            return ("https://app.globus.org/groups/{}").format(principal)
        return rule["principal_type"]

    formatted_print(
        rules,
        fields=[
            Field("Rule ID", "id"),
            Field("Permissions", "permissions"),
            Field("Shared With", principal_str),
            Field("Path", "path"),
        ],
    )
