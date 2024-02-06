from globus_cli.parsing import group


@group(
    "role",
    lazy_subcommands={
        "create": (".create", "create_command"),
        "delete": (".delete", "delete_command"),
        "list": (".list", "list_command"),
        "show": (".show", "show_command"),
    },
)
def role_command() -> None:
    """Manage Globus Connect Server (GCS) roles"""
