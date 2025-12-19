from globus_cli.parsing import group


@group(
    "tunnel",
    lazy_subcommands={
        "create": (".create", "create_tunnel_command"),
        "update": (".update", "update_tunnel_command"),
        "delete": (".delete", "delete_tunnel_command"),
        "list": (".list", "list_tunnel_command"),
        "show": (".show", "show_tunnel_command"),
        "stop": (".stop", "stop_tunnel_command"),
    },
)
def tunnel_command() -> None:
    """Manage Globus Tunnels."""
