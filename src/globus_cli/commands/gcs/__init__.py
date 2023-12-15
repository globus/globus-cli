from globus_cli.parsing import group


@group(
    "gcs",
    lazy_subcommands={
        "collection": ("collection", "collection_command"),
        # Note: endpoint is not an alias for the root 'endpoint' group as that group is
        #   broken up into slightly different subcommand structures here.
        "endpoint": (".endpoint", "endpoint_command"),
        "storage-gateway": ("endpoint.storage_gateway", "storage_gateway_command"),
        "user-credential": ("endpoint.user_credential", "user_credential_command"),
    },
)
def gcs_command() -> None:
    """Manage Globus Connect Server (GCS) resources"""
