from globus_cli.parsing import group


@group(
    "storage_gateway",
    lazy_subcommands={
        "list": (".list", "storage_gateway_list"),
    },
)
def storage_gateway_command() -> None:
    """Manage Storage Gateways on a GCS Endpoint"""
