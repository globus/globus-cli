from globus_cli.parsing import group


@group(
    "permission",
    lazy_subcommands={
        "create": (".create", "create_command"),
        "delete": (".delete", "delete_command"),
        "list": (".list", "list_command"),
        "show": (".show", "show_command"),
        "udpate": (".update", "update_command"),
    },
)
def permission_command() -> None:
    """Manage endpoint permissions (Access Control Lists)"""
