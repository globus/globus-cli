from globus_cli.parsing import group


@group(
    "access-point",
    lazy_subcommands={
        "show": (".show", "show_access_point_command"),
    },
)
def access_point_command() -> None:
    """Manage Globus Tunnels."""
