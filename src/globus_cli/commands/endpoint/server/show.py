from __future__ import annotations

import typing as t
import uuid
from textwrap import dedent

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import Field, TextMode, display, formatters

from ._common import server_id_arg

PORT_RANGE_T = t.Optional[t.Tuple[int, int]]


class PortRangeFormatter(
    formatters.FieldFormatter[t.Tuple[PORT_RANGE_T, PORT_RANGE_T]]
):
    def _parse_range(self, start: t.Any, end: t.Any) -> PORT_RANGE_T:
        if start is None or end is None:
            if start != end:
                raise ValueError("invalid port range, only one end is null")
            return None
        if not (isinstance(start, int) and isinstance(end, int)):
            raise ValueError("invalid port range, non-int values")
        return (start, end)

    def parse(self, value: t.Any) -> tuple[PORT_RANGE_T, PORT_RANGE_T]:
        if not isinstance(value, dict):
            raise ValueError("cannot parse port range from non-dict data")
        incoming_start, incoming_end = (
            value.get("incoming_data_port_start"),
            value.get("incoming_data_port_end"),
        )
        outgoing_start, outgoing_end = (
            value.get("outgoing_data_port_start"),
            value.get("outgoing_data_port_end"),
        )
        incoming_range = self._parse_range(incoming_start, incoming_end)
        outgoing_range = self._parse_range(outgoing_start, outgoing_end)
        return (incoming_range, outgoing_range)

    def _range_summary(self, prange: PORT_RANGE_T) -> str:
        if prange is None:
            return "unspecified"
        start, end = prange
        return "unrestricted" if start == 1024 and end == 65535 else f"{start}-{end}"

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
@LoginManager.requires_login("transfer")
def server_show(
    *, login_manager: LoginManager, endpoint_id: uuid.UUID, server_id: str
) -> None:
    """
    Display information about a server belonging to an endpoint.
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

    display(
        server_doc,
        text_mode=TextMode.text_record,
        fields=fields,
        text_epilog=text_epilog,
    )
