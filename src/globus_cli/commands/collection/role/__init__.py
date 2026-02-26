from globus_cli.parsing import group


@group(
    "role",
    lazy_subcommands={
        "list": (".list", "list_command"),
        "show": (".show", "show_command"),
        "create": (".create", "create_command"),
        "delete": (".delete", "delete_command"),
    },
)
def role_command() -> None:
    """Manage Roles on Collections."""
