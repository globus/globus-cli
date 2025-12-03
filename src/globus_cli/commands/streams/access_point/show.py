import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, display

STANDARD_FIELDS = [
    Field("ID", "id"),
    Field("Display Name", "attributes.display_name"),
    Field("Contact Email", "attributes.contact_email"),
    Field("Contact Info", "attributes.contact_info"),
    Field("Department", "attributes.department"),
    Field("Description", "attributes.description"),
    Field("Info Link", "attributes.info_link"),
    Field("Organization", "attributes.organization"),
]


@command("show", short_help="Show the attributes of a stream access point.")
@click.argument(
    "stream_access_point_id", metavar="STREAM_ACCESS_POINT_ID", type=click.UUID
)
@LoginManager.requires_login("auth", "transfer")
def show_access_point_command(
    login_manager: LoginManager,
    *,
    stream_access_point_id: uuid.UUID,
) -> None:
    """
    Show the attributes of a stream access point.
    """
    tunnel_client = login_manager.get_transfer_client()
    res = tunnel_client.get_stream_access_point(str(stream_access_point_id))
    display(
        res,
        text_mode=display.RECORD,
        fields=STANDARD_FIELDS,
        response_key="data",
    )
