from globus_cli.endpointish import Endpointish
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import TextMode, display


@command(
    "delete",
    short_help="Delete an endpoint",
    adoc_examples="""[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint delete $ep_id
----
""",
)
@endpoint_id_arg
@LoginManager.requires_login("transfer")
def endpoint_delete(*, login_manager: LoginManager, endpoint_id: str) -> None:
    """Delete a given endpoint.

    WARNING: Deleting an endpoint will permanently disable any existing shared
    endpoints that are hosted on it.
    """
    transfer_client = login_manager.get_transfer_client()
    Endpointish(
        endpoint_id, transfer_client=transfer_client
    ).assert_is_traditional_endpoint()

    res = transfer_client.delete_endpoint(endpoint_id)
    display(res, text_mode=TextMode.text_raw, response_key="message")
