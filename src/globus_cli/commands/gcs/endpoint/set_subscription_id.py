from __future__ import annotations

import typing as t
import uuid

import click

from globus_cli.constants import EXPLICIT_NULL, ExplicitNullType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import TextMode, display


class GCSSubscriptionIdType(click.ParamType):
    def get_type_annotation(self, _: click.Parameter) -> type:
        return t.cast(type, uuid.UUID | t.Literal["DEFAULT"] | ExplicitNullType)

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> t.Any:
        if ctx and ctx.resilient_parsing:
            return None

        if value.lower() == "null":
            return EXPLICIT_NULL
        elif value.lower() == "default":
            return "DEFAULT"
        try:
            return uuid.UUID(value)
        except ValueError:
            msg = (
                f"{value} is invalid. Expected either a UUID or the special "
                'values "DEFAULT" or "null"'
            )
            self.fail(msg, param, ctx)


@command("set-subscription-id", short_help="Set a GCS Endpoint's subscription.")
@endpoint_id_arg
@click.argument("SUBSCRIPTION_ID", type=GCSSubscriptionIdType())
@LoginManager.requires_login("transfer")
def set_subscription_id_command(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    subscription_id: uuid.UUID | t.Literal["DEFAULT"] | ExplicitNullType,
) -> None:
    """
    Update an endpoint's subscription.

    SUBSCRIPTION_ID must be one of: (1) A valid subscription ID (UUID), (2) the value
    "DEFAULT" (requires that you manage exactly one subscription & assigns the endpoint
    to that subscription), or (3) the value "null" (clears the endpoint's subscription).

    Setting a subscription requires that you are a subscription manager for the
    subscription being assigned.

    Removing a subscription requires that you are either (1) a subscription manager for
    the current assigned subscription group or (2) an admin of the endpoint.
    """
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)

    subscription_id_val = None if subscription_id is EXPLICIT_NULL else subscription_id
    res = gcs_client.put(
        "/endpoint/subscription_id",
        data={
            "DATA_TYPE": "endpoint_subscription#1.0.0",
            "subscription_id": subscription_id_val,
        },
    )

    display(res, text_mode=TextMode.text_raw, response_key="message")
