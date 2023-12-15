from globus_cli.parsing import group


@group(
    "gcp",
    lazy_subcommands={
        "create": (".create", "create_command"),
        "update": (".update", "update_command"),
        "set-subscription-id": (
            "endpoint.set_subscription_id",
            "set_endpoint_subscription_id",
        ),
    },
)
def gcp_command() -> None:
    """Manage Globus Connect Personal endpoints"""
