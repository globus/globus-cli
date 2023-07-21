from __future__ import annotations

import sys
import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import TextMode, display

from ._common import server_id_arg, server_update_opts

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


@command(
    "update",
    short_help="Update an endpoint server",
    adoc_examples="""Change an existing server's scheme to use ftp:

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ server_id=294682
$ globus endpoint server update $ep_id $server_id --scheme ftp
----
""",
)
@server_update_opts
@endpoint_id_arg
@server_id_arg
@LoginManager.requires_login("transfer")
def server_update(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    server_id: str,
    subject: str | None,
    port: int | None,
    scheme: Literal["gsiftp", "ftp"] | None,
    hostname: str | None,
    incoming_data_ports: tuple[int | None, int | None] | None,
    outgoing_data_ports: tuple[int | None, int | None] | None,
) -> None:
    """
    Update the attributes of a server on an endpoint.

    At least one field must be updated.
    """
    from globus_cli.services.transfer import assemble_generic_doc

    transfer_client = login_manager.get_transfer_client()

    server_doc = assemble_generic_doc(
        "server", subject=subject, port=port, scheme=scheme, hostname=hostname
    )

    # n.b. must be done after assemble_generic_doc(), as that function filters
    # out `None`s, which we need to be able to set for `'unspecified'`
    if incoming_data_ports:
        server_doc.update(
            incoming_data_port_start=incoming_data_ports[0],
            incoming_data_port_end=incoming_data_ports[1],
        )
    if outgoing_data_ports:
        server_doc.update(
            outgoing_data_port_start=outgoing_data_ports[0],
            outgoing_data_port_end=outgoing_data_ports[1],
        )

    res = transfer_client.update_endpoint_server(endpoint_id, server_id, server_doc)
    display(res, text_mode=TextMode.text_raw, response_key="message")
