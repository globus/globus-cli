from globus_cli.parsing import group


@group(
    "invite",
    lazy_subcommands={
        "accept": (".accept", "invite_accept"),
        "decline": (".decline", "invite_decline"),
    },
)
def group_invite() -> None:
    """Manage invitations to a Globus Group"""
