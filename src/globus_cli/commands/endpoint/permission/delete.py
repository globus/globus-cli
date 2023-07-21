import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import TextMode, display


@command(
    "delete",
    short_help="Delete an access control rule",
    adoc_examples="""[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ rule_id=1ddeddda-1ae8-11e7-bbe4-22000b9a448b
$ globus endpoint permission delete $ep_id $rule_id
----
""",
)
@endpoint_id_arg
@click.argument("rule_id")
@LoginManager.requires_login("transfer")
def delete_command(login_manager: LoginManager, *, endpoint_id, rule_id):
    """
    Delete an existing access control rule, removing whatever permissions it previously
    granted users on the endpoint.

    Note you cannot remove the built in rule that gives the endpoint owner full
    read and write access to the endpoint.
    """
    transfer_client = login_manager.get_transfer_client()

    res = transfer_client.delete_endpoint_acl_rule(endpoint_id, rule_id)
    display(res, text_mode=TextMode.text_raw, response_key="message")
