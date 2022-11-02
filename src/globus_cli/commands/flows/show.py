from __future__ import annotations

import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, flow_id_arg
from globus_cli.termio import Field, TextMode, display, formatters


@command("show")
@flow_id_arg
@LoginManager.requires_login(LoginManager.FLOWS_RS)
def show_command(login_manager: LoginManager, flow_id: uuid.UUID):
    """
    Show a flow
    """
    flows_client = login_manager.get_flows_client()
    auth_client = login_manager.get_auth_client()

    res = flows_client.get_flow(flow_id)

    principal_formatter = formatters.auth.PrincipalURNFormatter(auth_client)
    for principal_set_name in ("flow_administrators", "flow_viewers", "flow_starters"):
        for value in res.get(principal_set_name, ()):
            principal_formatter.add_item(value)
    principal_formatter.add_item(res.get("flow_owner"))

    fields = [
        Field("Flow ID", "id"),
        Field("Title", "title"),
        Field("Keywords", "keywords", formatter=formatters.ArrayFormatter()),
        Field("Owner", "flow_owner", formatter=principal_formatter),
        Field("Created At", "created_at", formatter=formatters.Date),
        Field("Updated At", "updated_at", formatter=formatters.Date),
        Field(
            "Administrators",
            "flow_administrators",
            formatter=formatters.ArrayFormatter(element_formatter=principal_formatter),
        ),
        Field(
            "Viewers",
            "flow_viewers",
            formatter=formatters.ArrayFormatter(element_formatter=principal_formatter),
        ),
        Field(
            "Starters",
            "flow_starters",
            formatter=formatters.ArrayFormatter(element_formatter=principal_formatter),
        ),
    ]

    display(res, fields=fields, text_mode=TextMode.text_record)
