from globus_cli.parsing import group


@group(
    "user_credential",
    lazy_subcommands={
        "create": (".create", "user_credential_create"),
        "delete": (".delete", "user_credential_delete"),
        "list": (".list", "user_credential_list"),
        "show": (".show", "user_credential_show"),
        "update": (".update", "user_credential_update"),
    },
)
def user_credential_command() -> None:
    """Manage User Credentials on a GCS Endpoint"""
