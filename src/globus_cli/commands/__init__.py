from globus_cli.parsing import main_group


@main_group(
    lazy_subcommands={
        "api": ("api", "api_command"),
        "bookmark": ("bookmark", "bookmark_command"),
        "cli-profile-list": ("cli_profile_list", "cli_profile_list"),
        "collection": ("collection", "collection_command"),
        "delete": ("delete", "delete_command"),
        "endpoint": ("endpoint", "endpoint_command"),
        "flows": ("flows", "flows_command"),
        "gcp": ("gcp", "gcp_command"),
        "gcs": ("gcs", "gcs_command"),
        "get-identities": ("get_identities", "get_identities_command"),
        "group": ("group", "group_command"),
        "list-commands": ("list_commands", "list_commands"),
        "login": ("login", "login_command"),
        "logout": ("logout", "logout_command"),
        "ls": ("ls", "ls_command"),
        "mkdir": ("mkdir", "mkdir_command"),
        "rename": ("rename", "rename_command"),
        "rm": ("rm", "rm_command"),
        "search": ("search", "search_command"),
        "session": ("session", "session_command"),
        "stat": ("stat", "stat_command"),
        "task": ("task", "task_command"),
        "timer": ("timer", "timer_command"),
        "transfer": ("transfer", "transfer_command"),
        "streams": ("streams", "stream_command"),
        "update": ("update", "update_command"),
        "version": ("version", "version_command"),
        "whoami": ("whoami", "whoami_command"),
    }
)
def main() -> None:
    """
    Interact with Globus from the command line

    All `globus` subcommands support `--help` documentation.

    Use `globus login` to get started!

    The documentation is also online at https://docs.globus.org/cli/
    """
