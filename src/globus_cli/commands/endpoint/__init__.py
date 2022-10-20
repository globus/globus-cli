from globus_cli.parsing import group


@group(
    "endpoint",
    lazy_subcommands={
        "activate": (".activate", "endpoint_activate"),
        "create": (".create", "endpoint_create"),
        "deactivate": (".deactivate", "endpoint_deactivate"),
        "delete": (".delete", "endpoint_delete"),
        "is-activated": (".is_activated", "endpoint_is_activated"),
        "local-id": (".local_id", "local_id"),
        "my-shared-endpoint-list": (
            ".my_shared_endpoint_list",
            "my_shared_endpoint_list",
        ),
        "permission": (".permission", "permission_command"),
        "role": (".role", "role_command"),
        "search": (".search", "endpoint_search"),
        "server": (".server", "server_command"),
        "set-subscription-id": (".set_subscription_id", "set_endpoint_subscription_id"),
        "show": (".show", "endpoint_show"),
        "storage-gateway": (".storage_gateway", "storage_gateway_command"),
        "update": (".update", "endpoint_update"),
        "user-credential": (".user_credential", "user_credential_command"),
    },
)
def endpoint_command() -> None:
    """Manage Globus endpoint definitions"""
