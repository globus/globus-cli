from __future__ import annotations

import typing as t
import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import (
    FORMAT_TEXT_RECORD,
    Field,
    field_formatters,
    formatted_print,
)

if t.TYPE_CHECKING:
    from globus_cli.services.auth import CustomAuthClient


class AclPrincipalFormatter(field_formatters.FieldFormatter[t.Tuple[str, str]]):
    def __init__(self, auth_client: CustomAuthClient):
        self.auth_client = auth_client

    def parse(self, value: t.Any) -> tuple[str, str]:
        if not isinstance(value, dict):
            raise ValueError("bad value for ACL principal, not a dict")

        return (str(value.get("principal_type")), str(value.get("principal")))

    def render(self, value: tuple[str, str]) -> str:
        principal_type, principal = value
        if principal_type == "identity":
            return str(self.auth_client.lookup_identity_name(principal))
        elif principal_type == "group":
            return f"https://app.globus.org/groups/{principal}"
        else:
            return principal_type


@command(
    "show",
    short_help="Display an access control rule",
    adoc_examples="""[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ rule_id=1ddeddda-1ae8-11e7-bbe4-22000b9a448b
$ globus endpoint permission show $ep_id $rule_id
----
""",
)
@endpoint_id_arg
@click.argument("rule_id")
@LoginManager.requires_login(LoginManager.AUTH_RS, LoginManager.TRANSFER_RS)
def show_command(*, login_manager: LoginManager, endpoint_id: uuid.UUID, rule_id: str):
    """
    Show detailed information about a single access control rule on an endpoint.
    """
    transfer_client = login_manager.get_transfer_client()
    auth_client = login_manager.get_auth_client()

    rule = transfer_client.get_endpoint_acl_rule(endpoint_id, rule_id)
    formatted_print(
        rule,
        text_format=FORMAT_TEXT_RECORD,
        fields=[
            Field("Rule ID", "id"),
            Field("Permissions", "permissions"),
            Field(
                "Shared With",
                "@",
                formatter=AclPrincipalFormatter(auth_client=auth_client),
            ),
            Field("Path", "path"),
        ],
    )
