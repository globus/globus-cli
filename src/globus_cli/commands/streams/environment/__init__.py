from globus_cli.parsing import group


@group(
    "environment",
    lazy_subcommands={
        "initialize": (".initialize", "initialize_command"),
        "update": (".update", "update_command"),
        "cleanup": (".cleanup", "cleanup_command"),
        "contact-lookup": (".contact_lookup", "contact_lookup"),
    },
)
def environment_command() -> None:
    """Manage Globus Streams application environments.

    These commands are used on the environments where Globus Stream
    enabled applications will run. They interact with The Globus Transfer
    service and the GCS endpoint associated with this side of the tunnel.
    You may be asked to log in twice in a row, once to Transfer and once
    to the local GCS service.

    Information about the tunnel is written to files under ~/.globus/tunnels.
    """
