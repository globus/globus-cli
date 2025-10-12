from __future__ import annotations

import uuid

import click

from globus_cli.constants import EXPLICIT_NULL, ExplicitNullType
from globus_cli.endpointish import Endpointish, EntityType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import display


class GCPSubscriptionIdType(click.ParamType):
    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> uuid.UUID | ExplicitNullType:
        if value.lower() == "null":
            return EXPLICIT_NULL

        try:
            return uuid.UUID(value)
        except ValueError:
            msg = (
                f"{value} is invalid. Expected either a UUID or the special value "
                '"null"'
            )
            self.fail(msg, param, ctx)


@command("set-subscription-id", short_help="Update a GCP endpoint's subscription.")
@endpoint_id_arg
@click.argument("SUBSCRIPTION_ID", type=GCPSubscriptionIdType())
@LoginManager.requires_login("transfer")
def set_endpoint_subscription_id(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    subscription_id: uuid.UUID | ExplicitNullType,
) -> None:
    """
    Update a GCP endpoint's subscription.

    This operation does not require you to be an admin of the endpoint. It is useful in
    cases where you are a subscription manager applying a subscription to an endpoint
    administered by someone else.

    SUBSCRIPTION_ID must be one of: (1) A valid subscription ID (UUID) or (2) the value
    "null" (clears the endpoint's subscription).
    """
    transfer_client = login_manager.get_transfer_client()
    epish = Endpointish(endpoint_id, transfer_client=transfer_client)
    epish.assert_entity_type(expect_types=EntityType.GCP_MAPPED)

    res = transfer_client.set_subscription_id(
        endpoint_id, ExplicitNullType.nullify(subscription_id)
    )

    display(res, text_mode=display.RAW, response_key="message")
