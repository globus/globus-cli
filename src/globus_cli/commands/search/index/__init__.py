from globus_cli.parsing import group


@group(
    "index",
    lazy_subcommands={
        "create": (".create", "create_command"),
        "delete": (".delete", "delete_command"),
        "list": (".list", "list_command"),
        "role": (".role", "role_command"),
        "show": (".show", "show_command"),
    },
)
def index_command() -> None:
    """View and manage indices"""
