from globus_cli.parsing import group


@group(
    "gcp",
    lazy_subcommands={
        "create": (".create", "create_command"),
        "update": (".update", "update_command"),
    },
)
def gcp_command():
    """Manage Globus Connect Personal endpoints"""
