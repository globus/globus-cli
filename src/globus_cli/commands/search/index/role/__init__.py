from globus_cli.parsing import group


@group(
    "role",
    lazy_subcommands={
        "create": (".create", "create_command"),
        "delete": (".delete", "delete_command"),
        "list": (".list", "list_command"),
    },
)
def role_command():
    """View and manage index roles"""
