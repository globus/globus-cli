from globus_cli.parsing import group


@group(
    "role",
    lazy_subcommands={
        "show": (".show", "show_command"),
    },
)
def role_command() -> None:
    """Manage roles on a Collection."""
