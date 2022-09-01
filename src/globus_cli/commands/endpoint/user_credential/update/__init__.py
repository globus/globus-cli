from globus_cli.parsing import group


@group(
    "user_credential",
    lazy_subcommands={
        "from-json": (".from_json", "from_json"),
    },
    hidden=True,
)
def user_credential_update() -> None:
    """Update a User Credential on an Endpoint"""
