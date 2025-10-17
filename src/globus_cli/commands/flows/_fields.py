import typing as t

import globus_sdk

from globus_cli.termio import Field, formatters
from globus_cli.termio.formatters.auth import PrincipalURNFormatter


class FlowPrincipalFormatter(PrincipalURNFormatter):
    """A principal formatter which properly pre-registers all principals for a flow."""

    def __init__(
        self, auth_client: globus_sdk.AuthClient, flow: dict[str, t.Any]
    ) -> None:
        super().__init__(auth_client)
        self.add_item(flow.get("flow_owner"))
        self.add_item(flow.get("flow_administrators", ()))
        self.add_item(flow.get("flow_viewers", ()))
        self.add_item(flow.get("run_managers", ()))
        self.add_item(flow.get("run_monitors", ()))


def flow_format_fields(
    auth_client: globus_sdk.AuthClient,
    flow: dict[str, t.Any],
) -> list[Field]:
    """
    The standard list of fields to render for a standard api flow-resource.

    :param auth_client: An AuthClient, used to resolve principal URNs.
    :param flow: The flow resource dict, used to pre-register principals for resolution.
    """
    principal = FlowPrincipalFormatter(auth_client, flow)
    principal_list = formatters.ArrayFormatter(element_formatter=principal)

    return [
        Field("Flow ID", "id"),
        Field("Title", "title"),
        Field("Subtitle", "subtitle"),
        Field("Description", "description"),
        Field("Keywords", "keywords", formatter=formatters.ArrayFormatter()),
        Field("Owner", "flow_owner", formatter=principal),
        Field("Subscription ID", "subscription_id"),
        Field("Created At", "created_at", formatter=formatters.Date),
        Field("Updated At", "updated_at", formatter=formatters.Date),
        Field("Administrators", "flow_administrators", formatter=principal_list),
        Field("Viewers", "flow_viewers", formatter=principal_list),
        Field("Starters", "flow_starters", formatter=principal_list),
        Field("Run Managers", "run_managers", formatter=principal_list),
        Field("Run Monitors", "run_monitors", formatter=principal_list),
    ]
