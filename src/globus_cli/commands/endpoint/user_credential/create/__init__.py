from globus_cli.parsing import group


@group(
    "user_credential",
    lazy_subcommands={
        "from-json": (".from_json", "from_json"),
        "posix": (".posix", "posix"),
        "s3": (".s3", "s3"),
    },
)
def user_credential_create() -> None:
    """Create a User Credential on an Endpoint"""
