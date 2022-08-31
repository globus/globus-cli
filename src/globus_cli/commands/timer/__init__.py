from globus_cli.parsing import group


@group(
    "timer",
    lazy_subcommands={
        "delete": (".delete", "delete_command"),
        "list": (".list", "list_command"),
        "show": (".show", "show_command"),
    },
)
def timer_command():
    """Schedule and manage jobs in Globus Timer"""
