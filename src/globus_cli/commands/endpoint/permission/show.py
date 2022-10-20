import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import FORMAT_TEXT_RECORD, Field, formatted_print


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
def show_command(*, login_manager: LoginManager, endpoint_id, rule_id):
    """
    Show detailed information about a single access control rule on an endpoint.
    """
    transfer_client = login_manager.get_transfer_client()
    auth_client = login_manager.get_auth_client()

    def _shared_with_keyfunc(rule):
        if rule["principal_type"] == "identity":
            return auth_client.lookup_identity_name(rule["principal"])
        elif rule["principal_type"] == "group":
            return "https://app.globus.org/groups/{}".format(rule["principal"])
        else:
            return rule["principal_type"]

    rule = transfer_client.get_endpoint_acl_rule(endpoint_id, rule_id)
    formatted_print(
        rule,
        text_format=FORMAT_TEXT_RECORD,
        fields=[
            Field("Rule ID", "id"),
            Field("Permissions", "permissions"),
            Field("Shared With", _shared_with_keyfunc),
            Field("Path", "path"),
        ],
    )
