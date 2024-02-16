from __future__ import annotations

import functools
import typing as t
import uuid

import click
import globus_sdk

from globus_cli.commands.gcs.endpoint._common import GCS_ENDPOINT_FIELDS
from globus_cli.constants import EXPLICIT_NULL, ExplicitNullType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import CommaDelimitedList, command, endpoint_id_arg
from globus_cli.parsing.param_types.nullable import IntOrNull
from globus_cli.termio import TextMode, display


class SubscriptionIdType(click.ParamType):
    def get_type_annotation(self, _: click.Parameter) -> type:
        return t.cast(type, str | ExplicitNullType)

    def get_metavar(self, _: click.Parameter) -> t.Optional[str]:
        return "[<uuid>|DEFAULT|null]"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> t.Any:
        if value is None or (ctx and ctx.resilient_parsing):
            return None
        if value.lower() == "null":
            return EXPLICIT_NULL
        if value.lower() == "default":
            return "DEFAULT"
        try:
            uuid.UUID(value)
            return value
        except ValueError:
            self.fail(f"{value} is not a valid Subscription ID", param, ctx)


def network_use_constraints(func: t.Callable) -> t.Callable:
    """
    Enforces that custom network use related parameters are present when network use is
    set to custom.
    """

    _CUSTOM_NETWORK_USE_PARAMS = frozenset(
        {
            "max_concurrency",
            "max_parallelism",
            "preferred_concurrency",
            "preferred_parallelism",
        }
    )

    @functools.wraps(func)
    def wrapped(*args: t.Any, **kwargs: t.Any) -> t.Any:
        if kwargs.get("network_use") == "custom":
            if any(kwargs.get(k) is None for k in _CUSTOM_NETWORK_USE_PARAMS):
                raise click.UsageError(
                    "When network-use is set to custom, you must also provide "
                    "max-concurrency, max-parallelism, preferred-concurrency, and "
                    "preferred-parallelism"
                )
        return func(*args, **kwargs)

    return wrapped


@command("update")
@endpoint_id_arg
@click.option(
    "--allow-udt",
    type=bool,
    help="A flag indicating whether UDT is allowed for this endpoint.",
)
@click.option(
    "--contact-email",
    type=str,
    help="Email address of the end-user-facing support contact for this endpoint.",
)
@click.option(
    "--contact-info",
    type=str,
    help=(
        "Other end-user-facing non-email contact information for the endpoint, e.g. "
        "phone and mailing address."
    ),
)
@click.option(
    "--department",
    type=str,
    help=(
        "[Searchable] The department within an organization which runs the server(s) "
        "represented by this endpoint."
    ),
)
@click.option(
    "--description",
    type=str,
    help="A human-readable description of the endpoint (max: 4096 characters).",
)
@click.option(
    "--display-name",
    type=str,
    help="[Searchable] A human-readable, non-unique name for the endpoint.",
)
@click.option(
    "--gridftp-control-channel-port",
    type=IntOrNull(),
    help="The TCP port which the Globus control channel should listen on.",
)
@click.option(
    "--info-link",
    type=str,
    help=(
        "An end-user-facing URL for a webpage with more information about the endpoint."
    ),
)
@click.option(
    "--keywords",
    type=CommaDelimitedList(),
    help="[Searchable] A comma-separated list of search keywords.",
)
@click.option(
    "--max-concurrency",
    type=int,
    help=(
        "The endpoint network's custom max concurrency. Requires `network-use` be "
        "set to `custom`."
    ),
)
@click.option(
    "--max-parallelism",
    type=int,
    help=(
        "The endpoint network's custom max parallelism. Requires `network-use` be "
        "set to `custom`."
    ),
)
@click.option(
    "--network-use",
    type=click.Choice(["normal", "minimal", "aggressive", "custom"]),
    help=(
        "A control valve for how Globus will interact with this endpoint over the "
        "network. If custom, you must also provide max and preferred concurrency "
        "as well as max and preferred parallelism."
    ),
)
@click.option(
    "--organization",
    type=str,
    help="The organization which runs the server(s) represented by the endpoint.",
)
@click.option(
    "--preferred-concurrency",
    type=int,
    help=(
        "The endpoint network's custom preferred concurrency. Requires `network-use` "
        "be set to `custom`."
    ),
)
@click.option(
    "--preferred-parallelism",
    type=int,
    help=(
        "The endpoint network's custom preferred parallelism. Requires `network-use` "
        "be set to `custom`."
    ),
)
@click.option(
    "--public/--private",
    is_flag=True,
    default=None,
    help=(
        "A flag indicating whether this endpoint is visible to all other Globus users. "
        "If private, it will only be visible to users which have been granted a "
        "role on the endpoint, have been granted a role on one of its collections, or "
        "belong to a domain which has access to any of its storage gateways."
    ),
)
@click.option(
    "--subscription-id",
    type=SubscriptionIdType(),
    help=(
        "'<uuid>' will set an exact subscription. 'null' will remove the current "
        "subscription. 'DEFAULT' will instruct GCS to infer and set the subscription "
        "from your user (requires that you are a subscription manager of exactly one "
        "subscription)"
    ),
)
@network_use_constraints
@LoginManager.requires_login("transfer")
def update_command(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    allow_udt: bool | None,
    contact_email: str | None,
    contact_info: str | None,
    department: str | None,
    description: str | None,
    display_name: str | None,
    gridftp_control_channel_port: int | None | ExplicitNullType,
    info_link: str | None,
    keywords: list[str] | None,
    max_concurrency: int | None,
    max_parallelism: int | None,
    network_use: t.Literal["normal", "minimal", "aggressive", "custom"] | None,
    organization: str | None,
    preferred_concurrency: int | None,
    preferred_parallelism: int | None,
    public: bool | None,
    subscription_id: str | None | ExplicitNullType,
) -> None:
    """Update a GCS Endpoint."""
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)

    endpoint_data = {
        "allow_udt": allow_udt,
        "contact_email": contact_email,
        "contact_info": contact_info,
        "department": department,
        "description": description,
        "display_name": display_name,
        "gridftp_control_channel_port": gridftp_control_channel_port,
        "info_link": info_link,
        "keywords": keywords,
        "max_concurrency": max_concurrency,
        "max_parallelism": max_parallelism,
        "network_use": network_use,
        "organization": organization,
        "preferred_concurrency": preferred_concurrency,
        "preferred_parallelism": preferred_parallelism,
        "public": public,
        "subscription_id": subscription_id,
    }
    endpoint_document = globus_sdk.EndpointDocument(
        **ExplicitNullType.nullify_dict(endpoint_data)  # type: ignore[arg-type]
    )

    res = gcs_client.update_endpoint(endpoint_document, include="endpoint")

    display(res, text_mode=TextMode.text_record, fields=GCS_ENDPOINT_FIELDS)
