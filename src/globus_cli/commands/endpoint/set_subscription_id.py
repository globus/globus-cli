from __future__ import annotations

import typing as t
import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import TextMode, display


class SubscriptionIdType(click.ParamType):
    def get_type_annotation(self, param: click.Parameter) -> type:
        return t.cast(type, str)

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> t.Any:
        if value is None or (ctx and ctx.resilient_parsing):
            return None
        if value.lower() == "null":
            return "null"
        try:
            uuid.UUID(value)
            return value
        except ValueError:
            self.fail(f"{value} is not a valid Subscription ID", param, ctx)


@command(
    "set-subscription-id",
    deprecated=True,
    short_help="Set an endpoint's subscription",
)
@endpoint_id_arg
@click.argument("SUBSCRIPTION_ID", type=SubscriptionIdType())
@LoginManager.requires_login("transfer")
def set_endpoint_subscription_id(
    login_manager: LoginManager, *, endpoint_id: uuid.UUID, subscription_id: str
) -> None:
    """
    For GCS endpoints, refer to ``globus gcs endpoint set-subscription-id``. For
    GCP endpoints, refer to ``globus gcp set-subscription-id``.

    -----------------------------

    Set an endpoint's subscription ID.

    Unlike the '--managed' flag for 'globus endpoint update', this operation does not
    require you to be an admin of the endpoint. It is useful in cases where you are a
    subscription manager applying a subscription to an endpoint with a different admin.

    SUBSCRIPTION_ID should either be a valid subscription ID or 'null'.
    """
    transfer_client = login_manager.get_transfer_client()

    optional_subscription_id: str | None = (
        None if subscription_id == "null" else subscription_id
    )
    res = transfer_client.put(
        f"/endpoint/{endpoint_id}/subscription",
        data={"subscription_id": optional_subscription_id},
    )
    display(res, text_mode=TextMode.text_raw, response_key="message")
