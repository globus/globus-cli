from __future__ import annotations

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, no_local_server_option


@command(
    "consent",
    short_help="Update your session with specific consents",
    disable_options=["format", "map_http_status"],
)
@no_local_server_option
@click.argument("SCOPES", nargs=-1, required=True)
def session_consent(scopes: tuple[str], no_local_server: bool) -> None:
    """
    Update your current CLI auth session by authenticating with a specific scope or set
    of scopes.

    This command is necessary when the CLI needs access to resources which require the
    user to explicitly consent to access.
    """
    manager = LoginManager()
    manager.run_login_flow(
        no_local_server=no_local_server,
        local_server_message=(
            "You are running 'globus session consent', "
            "which should automatically open a browser window for you to "
            "authenticate with specific identities.\n"
            "If this fails or you experience difficulty, try "
            "'globus session consent --no-local-server'"
            "\n---"
        ),
        epilog="\nYou have successfully updated your CLI session.\n",
        scopes=list(scopes),
    )
