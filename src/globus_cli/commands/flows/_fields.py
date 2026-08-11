import typing as t

import globus_sdk

from globus_cli.termio import Field, formatters
from globus_cli.termio.formatters import (
    ArrayFormatter,
    FieldFormatter,
)
from globus_cli.termio.formatters.auth import PrincipalURNFormatter


class FlowPrincipalFormatter(PrincipalURNFormatter):
    """A principal formatter which properly pre-registers all principals for a flow."""

    def __init__(
        self, auth_client: globus_sdk.AuthClient, flow: dict[str, t.Any]
    ) -> None:
        super().__init__(auth_client)
        self.add_items(flow.get("flow_owner"))
        self.add_items(*flow.get("flow_administrators", ()))
        self.add_items(*flow.get("flow_viewers", ()))
        self.add_items(*flow.get("run_managers", ()))
        self.add_items(*flow.get("run_monitors", ()))


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
    fuzzy_bool = formatters.FuzzyBool

    return [
        Field("Flow ID", "id"),
        Field("Title", "title"),
        Field("Subtitle", "subtitle"),
        Field("Description", "description"),
        Field("Keywords", "keywords", formatter=csv_list),
        Field("Owner", "flow_owner", formatter=principal),
        Field("High Assurance", "authentication_policy_id", formatter=fuzzy_bool),
        Field("Authentication Policy ID", "authentication_policy_id"),
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
        self.add_items(flow_run.get("run_owner"))
        self.add_items(*flow_run.get("run_managers", ()))
        self.add_items(*flow_run.get("run_monitors", ()))


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


class RegisteredAPIPrincipalFormatter(PrincipalURNFormatter):
    """A principal formatter which pre-registers all principals for a registered API."""

    def __init__(
        self, auth_client: globus_sdk.AuthClient, registered_api: dict[str, t.Any]
    ) -> None:
        super().__init__(auth_client)
        roles = registered_api.get("roles", {})
        self.add_items(*roles.get("owners", ()))
        self.add_items(*roles.get("administrators", ()))
        self.add_items(*roles.get("viewers", ()))


def registered_api_format_fields(
    auth_client: globus_sdk.AuthClient,
    registered_api: dict[str, t.Any],
) -> list[Field]:
    """
    The standard list of fields to render for a registered API resource.

    :param auth_client: An AuthClient, used to resolve principal URNs.
    :param registered_api: The registered API resource, used to pre-register
        principals.
    """
    principal = RegisteredAPIPrincipalFormatter(auth_client, registered_api)
    csv_principal_list = formatters.ArrayFormatter(
        element_formatter=principal,
        delimiter=", ",
    )

    return [
        Field("Registered API ID", "id"),
        Field("Name", "name"),
        Field("Description", "description"),
        Field("Status", "status"),
        Field("Subscription ID", "subscription_id"),
        Field("Created At", "created_timestamp", formatter=formatters.Date),
        Field("Updated At", "updated_timestamp", formatter=formatters.Date),
        Field("Edited At", "edited_timestamp", formatter=formatters.Date),
        Field(
            "Scheduled Deletion",
            "scheduled_deletion_timestamp",
            formatter=formatters.Date,
        ),
        Field("Owners", "roles.owners", formatter=csv_principal_list),
        Field("Administrators", "roles.administrators", formatter=csv_principal_list),
        Field("Viewers", "roles.viewers", formatter=csv_principal_list),
        Field("Target Type", "target.type"),
        Field("OpenAPI Version", "target.openapi_version"),
        Field("Destination Method", "target.destination.method"),
        Field("Destination URL", "target.destination.url"),
    ]


class WebInputPrincipalFormatter(PrincipalURNFormatter):
    """A principal formatter which pre-registers all principals for a web input."""

    def __init__(
        self, auth_client: globus_sdk.AuthClient, web_input: dict[str, t.Any]
    ) -> None:
        super().__init__(auth_client)
        self.add_items(web_input.get("creator_urn"))
        roles = web_input.get("roles", {})
        self.add_items(*roles.get("viewer_urns", ()))
        self.add_items(*roles.get("respondent_urns", ()))


class IdentifiedResourceFormatter(FieldFormatter[str]):
    def parse(self, value: t.Any) -> str:
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError("cannot format parenthetical from data of wrong shape")
        name, resource_id = value[0], value[1]
        if not isinstance(resource_id, str):
            raise ValueError("cannot format parenthetical non-str id")
        if isinstance(name, str):
            # If the name can be parsed, render it alongside the resource id
            return f"{name} ({resource_id})"
        # If the name can't be parsed, just render the resource id
        return resource_id

    def render(self, value: str) -> str:
        return value


class _OptionFormatter(FieldFormatter[tuple[t.Any, t.Any]]):
    def parse(self, value: t.Any) -> tuple[t.Any, t.Any]:
        if not isinstance(value, dict):
            raise ValueError("non-dict field value")
        elif "option_id" not in value or "label" not in value:
            raise ValueError("missing key 'option_id' and/or 'label'")
        return value["option_id"], value["label"]

    def render(self, value: tuple[t.Any, t.Any]) -> str:
        option_id, label = value
        return f"*  {option_id}  {label}"


class _WebInputContextRowsFormatter(FieldFormatter[t.List[t.Tuple[str, str]]]):
    """Renders a list of {field, value} rows as an aligned 'field: value' block."""

    def parse(self, value: t.Any) -> list[tuple[str, str]]:
        if not isinstance(value, list):
            raise ValueError("non list context rows value")
        rows = []
        for item in value:
            if not isinstance(item, dict) or "field" not in item or "value" not in item:
                raise ValueError("missing key 'field' and/or 'value'")
            rows.append((item["field"], item["value"]))
        return rows

    def render(self, value: list[tuple[str, str]]) -> str:
        width = max(len(field) for field, _ in value) + 2
        return "\n".join(f"{field}:".ljust(width) + str(val) for field, val in value)


def web_input_format_fields(
    auth_client: globus_sdk.AuthClient,
    web_input: dict[str, t.Any],
) -> list[Field]:
    """
    The standard list of fields to render for a web input resource.

    :param auth_client: An AuthClient, used to resolve principal URNs.
    :param web_input: The web input resource, used to pre-register principals.
    """
    principal = WebInputPrincipalFormatter(auth_client, web_input)
    csv_principal_list = formatters.ArrayFormatter(
        element_formatter=principal,
        delimiter=", ",
    )
    csv_list = formatters.ArrayFormatter(delimiter=", ")
    flow_run_formatter = IdentifiedResourceFormatter()

    fields = [
        Field("Web Input ID", "id"),
        Field("Status", "status"),
        Field("Title", "context.title"),
        Field("Your Roles", "user_roles", formatter=csv_list),
        Field("Flow", "[flow.title, flow.id]", formatter=flow_run_formatter),
        Field("Run", "[run.label, run.id]", formatter=flow_run_formatter),
        Field("Creator", "creator_urn", formatter=principal),
        Field("Viewers", "roles.viewer_urns", formatter=csv_principal_list),
        Field("Respondents", "roles.respondent_urns", formatter=csv_principal_list),
        Field("Created At", "created_timestamp", formatter=formatters.Date),
        Field("Closed At", "closed_timestamp", formatter=formatters.Date),
    ]

    if web_input.get("context", {}).get("presentation_style") == "table":
        fields += [
            Field(
                "Context",
                "context.rows",
                section=True,
                formatter=_WebInputContextRowsFormatter(),
            )
        ]
    else:
        fields += [Field("Context", "context.text", section=True)]

    if web_input.get("options"):
        formatter = ArrayFormatter(delimiter="\n", element_formatter=_OptionFormatter())
        fields += [Field("Options", "options", section=True, formatter=formatter)]

    return fields
