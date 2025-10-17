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
    :param flow: The flow resource, used to pre-register formattable principals.
    """
    principal = FlowPrincipalFormatter(auth_client, flow)
    csv_principal_list = formatters.ArrayFormatter(
        element_formatter=principal,
        delimiter=", ",
    )
    csv_list = formatters.ArrayFormatter(delimiter=", ")

    return [
        Field("Flow ID", "id"),
        Field("Title", "title"),
        Field("Subtitle", "subtitle"),
        Field("Description", "description"),
        Field("Keywords", "keywords", formatter=csv_list),
        Field("Owner", "flow_owner", formatter=principal),
        Field("Subscription ID", "subscription_id"),
        Field("Created At", "created_at", formatter=formatters.Date),
        Field("Updated At", "updated_at", formatter=formatters.Date),
        Field("Administrators", "flow_administrators", formatter=csv_principal_list),
        Field("Viewers", "flow_viewers", formatter=csv_principal_list),
        Field("Starters", "flow_starters", formatter=csv_principal_list),
        Field("Run Managers", "run_managers", formatter=csv_principal_list),
        Field("Run Monitors", "run_monitors", formatter=csv_principal_list),
    ]


class FlowRunPrincipalFormatter(PrincipalURNFormatter):
    """A principal formatter which pre-registers all principals for a flow run."""

    def __init__(
        self, auth_client: globus_sdk.AuthClient, flow_run: dict[str, t.Any]
    ) -> None:
        super().__init__(auth_client)
        self.add_item(flow_run.get("run_owner"))
        self.add_item(flow_run.get("run_managers", ()))
        self.add_item(flow_run.get("run_monitors", ()))


def flow_run_format_fields(
    auth_client: globus_sdk.AuthClient,
    flow_run: dict[str, t.Any],
) -> list[Field]:
    """
    The standard list of fields to render for a standard api flow-run resource.

    :param auth_client: An AuthClient, used to resolve principal URNs.
    :param flow_run: The flow run resource, used to pre-register formattable principals.
    """
    principal = FlowRunPrincipalFormatter(auth_client, flow_run)
    csv_principal_list = formatters.ArrayFormatter(
        element_formatter=principal,
        delimiter=", ",
    )
    csv_list = formatters.ArrayFormatter(delimiter=", ")

    flow_description_fields = (
        [
            Field("Flow Subtitle", "flow_description.subtitle"),
            Field("Flow Description", "flow_description.description"),
            Field("Flow Keywords", "flow_description.keywords", formatter=csv_list),
        ]
        if "flow_description" in flow_run
        else []
    )

    return [
        Field("Run ID", "run_id"),
        Field("Run Label", "label"),
        Field("Run Tags", "tags", formatter=csv_list),
        Field("Status", "status"),
        Field("Started At", "start_time", formatter=formatters.Date),
        Field("Completed At", "completion_time", formatter=formatters.Date),
        Field("Flow ID", "flow_id"),
        Field("Flow Title", "flow_title"),
        *flow_description_fields,
        Field("Run Owner", "run_owner", formatter=principal),
        Field("Run Managers", "run_managers", formatter=csv_principal_list),
        Field("Run Monitors", "run_monitors", formatter=csv_principal_list),
    ]
