from __future__ import annotations

import typing as t
import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import Field, field_formatters, formatted_print


class AclPrincipalFormatter(field_formatters.PrincipalWithTypeKeyFormatter):
    # customize the formatter to provide the `principal_type` as the fallback value for
    # unrecognized types. This handles various cases in which
    # `principal_type=all_authenticated_users` or similar
    def parse(self, value: t.Any) -> tuple[str, str, str]:
        parsed_type, parsed_value, fallback = super().parse(value)
        return (parsed_type, parsed_value, parsed_type)


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

    formatter = AclPrincipalFormatter(
        auth_client,
        values_are_urns=False,
        group_format_str="https://app.globus.org/groups/{group_id}",
    )
    formatter.add_items(rules)

    formatted_print(
        rules,
        fields=[
            Field("Rule ID", "id"),
            Field("Permissions", "permissions"),
            Field("Shared With", "@", formatter=formatter),
            Field("Path", "path"),
        ],
    )
