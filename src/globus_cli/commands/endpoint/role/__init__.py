from globus_cli.parsing import group


@group(
    "role",
    lazy_subcommands={
        "create": (".create", "role_create"),
        "delete": (".delete", "role_delete"),
        "list": (".list", "role_list"),
        "show": (".show", "role_show"),
    },
)
def role_command() -> None:
    """Manage endpoint roles"""
