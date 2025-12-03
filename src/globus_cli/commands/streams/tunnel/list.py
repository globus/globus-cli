from __future__ import annotations

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, display

TUNNEL_LIST_FIELDS = [
    Field("ID", "id"),
    Field("Label", "attributes.label"),
    Field("State", "attributes.state"),
    Field("Created Time", "attributes.created_time"),
]


@command("list", short_help="List Globus tunnels.")
@LoginManager.requires_login("auth", "transfer")
def list_tunnel_command(
    login_manager: LoginManager,
) -> None:
    """
    List all the Globus tunnels that this user can see.
    """
    tunnel_client = login_manager.get_transfer_client()
    res = tunnel_client.list_tunnels()
    display(
        res,
        text_mode=display.TABLE,
        fields=TUNNEL_LIST_FIELDS,
        response_key="data",
    )
