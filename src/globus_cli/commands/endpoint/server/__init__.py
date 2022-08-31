from globus_cli.parsing import group


@group(
    "server",
    short_help="Manage servers for a Globus endpoint",
    lazy_subcommands={
        "add": (".add", "server_add"),
        "delete": (".delete", "server_delete"),
        "list": (".list", "server_list"),
        "show": (".show", "server_show"),
        "update": (".update", "server_update"),
    },
)
def server_command() -> None:
    """
    Manage the servers which back a Globus endpoint

    This typically refers to a Globus Connect Server endpoint running on multiple
    servers. Each GridFTP server is registered as a server backing the endpoint.
    """
