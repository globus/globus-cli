from globus_cli.parsing import group


@group(
    "create",
    lazy_subcommands={
        "mapped": (".mapped", "mapped_command"),
        "guest": (".guest", "guest_command"),
    },
)
def create_command():
    """Create Globus Connect Personal collections"""
