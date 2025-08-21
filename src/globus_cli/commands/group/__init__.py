from globus_cli.parsing import group


@group(
    "group",
    lazy_subcommands={
        "create": (".create", "group_create"),
        "delete": (".delete", "group_delete"),
        "invite": (".invite", "group_invite"),
        "join": (".join", "group_join"),
        "leave": (".leave", "group_leave"),
        "list": (".list", "group_list"),
        "member": (".member", "group_member"),
        "set-policies": (".set_policies", "group_set_policies"),
        "show": (".show", "group_show"),
        "get-subscription-info": (
            ".get_subscription_info",
            "group_get_subscription_info",
        ),
        "get-by-subscription": (".get_by_subscription", "group_get_by_subscription"),
        "update": (".update", "group_update"),
        "set-subscription-admin-verified": (
            ".set_subscription_admin_verified",
            "group_set_subscription_admin_verified",
        ),
    },
)
def group_command() -> None:
    """Manage Globus Groups."""
