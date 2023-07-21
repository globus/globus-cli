from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import TextMode, display


@command(
    "deactivate",
    short_help="Deactivate an endpoint",
    adoc_examples="""Deactivate an endpoint:

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint deactivate $ep_id
----
""",
)
@endpoint_id_arg
@LoginManager.requires_login("transfer")
def endpoint_deactivate(login_manager: LoginManager, *, endpoint_id: str) -> None:
    """
    Remove the credential previously assigned to an endpoint via
    'globus endpoint activate' or any other form of endpoint activation
    """
    transfer_client = login_manager.get_transfer_client()
    res = transfer_client.endpoint_deactivate(endpoint_id)
    display(res, text_mode=TextMode.text_raw, response_key="message")
