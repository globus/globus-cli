from __future__ import annotations

import typing as t
from textwrap import dedent

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import (
    FORMAT_TEXT_RECORD,
    Field,
    field_formatters,
    formatted_print,
)

from ._common import server_id_arg

PORT_RANGE_T = t.Tuple[int | None, int | None]


class PortRangeFormatter(
    field_formatters.FieldFormatter[t.Tuple[PORT_RANGE_T, PORT_RANGE_T]]
):
    def parse(self, value: t.Any) -> tuple[PORT_RANGE_T, PORT_RANGE_T]:
        incoming_start, incoming_end = (
            value.get("incoming_data_port_start"),
            value.get("incoming_data_port_end"),
        )
        if not (incoming_start is None or isinstance(incoming_start, int)):
            raise ValueError("invalid incoming_data_port_start")
        if not (incoming_end is None or isinstance(incoming_end, int)):
            raise ValueError("invalid incoming_data_port_end")
        outgoing_start, outgoing_end = (
            value.get("outgoing_data_port_start"),
            value.get("outgoing_data_port_end"),
        )
        if not (outgoing_start is None or isinstance(outgoing_start, int)):
            raise ValueError("invalid outgoing_data_port_start")
        if not (outgoing_end is None or isinstance(outgoing_end, int)):
            raise ValueError("invalid outgoing_data_port_end")

        return ((incoming_start, incoming_end), (outgoing_start, outgoing_end))

    def _range_summary(self, start: int | None, end: int | None) -> str:
        return (
            "unspecified"
            if not start and not end
            else "unrestricted"
            if start == 1024 and end == 65535
            else f"{start}-{end}"
        )

    def render(self, value: tuple[PORT_RANGE_T, PORT_RANGE_T]) -> str:
        incoming = self._range_summary(value[0])
        outgoing = self._range_summary(value[1])
        return f"incoming {incoming}, outgoing {outgoing}"


@command(
    "show",
    short_help="Show an endpoint server",
    adoc_examples="""[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ server_id=207976
$ globus endpoint server show $ep_id $server_id
----
""",
)
@endpoint_id_arg
@server_id_arg
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def server_show(*, login_manager: LoginManager, endpoint_id, server_id):
    """
    Display inofrmation about a server belonging to an endpoint.
    """
    transfer_client = login_manager.get_transfer_client()

    server_doc = transfer_client.get_endpoint_server(endpoint_id, server_id)
    fields = [Field("ID", "id")]
    if not server_doc["uri"]:  # GCP endpoint server
        text_epilog: str | None = dedent(
            """
            This server is for a Globus Connect Personal installation.

            For its connection status, try:
            globus endpoint show {}
        """.format(
                endpoint_id
            )
        )
    else:
        fields.extend(
            [
                Field("URI", "uri"),
                Field("Subject", "subject"),
                Field("Data Ports", "@", formatter=PortRangeFormatter()),
            ]
        )
        text_epilog = None

    formatted_print(
        server_doc,
        text_format=FORMAT_TEXT_RECORD,
        fields=fields,
        text_epilog=text_epilog,
    )
