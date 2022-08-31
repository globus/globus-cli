from globus_cli.parsing import group


@group(
    "member",
    lazy_subcommands={
        "add": (".add", "member_add"),
        "approve": (".approve", "member_approve"),
        "invite": (".invite", "member_invite"),
        "list": (".list", "member_list"),
        "reject": (".reject", "member_reject"),
        "remove": (".remove", "member_remove"),
    },
)
def group_member() -> None:
    """Manage members in a Globus Group"""
