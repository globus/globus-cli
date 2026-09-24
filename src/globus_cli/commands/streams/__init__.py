from globus_cli.parsing import group


@group(
    "streams",
    lazy_subcommands={
        "tunnel": (".tunnel", "tunnel_command"),
        "access-point": (".access_point", "access_point_command"),
        "environment": (".environment", "environment_command"),
    },
)
def stream_command() -> None:
    """Manage Globus Tunnels."""
