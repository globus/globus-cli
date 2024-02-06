from globus_cli.parsing import group


@group(
    "endpoint",
    lazy_subcommands={
        "role": (".role", "role_command"),
        "set-subscription-id": (".set_subscription_id", "set_subscription_id_command"),
    },
)
def endpoint_command() -> None:
    """Manage Globus Connect Server (GCS) endpoints"""
