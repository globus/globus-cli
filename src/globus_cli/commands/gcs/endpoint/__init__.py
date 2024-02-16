from globus_cli.parsing import group


@group(
    "endpoint",
    lazy_subcommands={
        "set-subscription-id": (".set_subscription_id", "set_subscription_id_command"),
        "show": (".show", "show_command"),
        "update": (".update", "update_command"),
    },
)
def endpoint_command() -> None:
    """Manage Globus Connect Server (GCS) endpoints"""
