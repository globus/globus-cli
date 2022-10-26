import time

import globus_sdk

from globus_cli.login_manager import (
    LoginManager,
    get_client_login,
    internal_auth_client,
    is_client_login,
    token_storage_adapter,
)
from globus_cli.parsing import command
from globus_cli.termio import display, print_command_hint


@command(
    "show",
    short_help="Show your current CLI auth session",
    adoc_output="""Note: this output will not show your primary identity if it is not
in session. For information on your identity set use 'globus whoami'.

When textual output is requested, the output will be a table with
the following fields:

- 'Username'
- 'ID'
- 'Auth Time'

When JSON output is requested the output will also have the session id
if needed.
""",
    adoc_examples="""Display the current session with JSON output

[source,bash]
----
$ globus session show --format json
----
""",
)
@LoginManager.requires_login(LoginManager.AUTH_RS)
def session_show(*, login_manager):
    """List all identities in your current CLI auth session.

    Lists identities that are in the session tied to the CLI's access tokens along with
    the time the user authenticated with that identity.
    """
    auth_client = login_manager.get_auth_client()
    adapter = token_storage_adapter()

    # get a token to introspect, refreshing if neccecary
    try:
        # may force a refresh if the token is expired
        auth_client.authorizer.get_authorization_header()
    except AttributeError:  # if we have no RefreshTokenAuthorizor
        pass

    tokendata = adapter.get_token_data(LoginManager.AUTH_RS)
    # if there's no token (e.g. not logged in), stub with empty data
    if not tokendata:
        session_info = {}
        authentications = {}
    else:
        if is_client_login():
            introspect_client = get_client_login()
        else:
            introspect_client = internal_auth_client()

        access_token = tokendata["access_token"]
        res = introspect_client.oauth2_token_introspect(
            access_token, include="session_info"
        )

        session_info = res.get("session_info", {})
        authentications = session_info.get("authentications") or {}

    # resolve ids to human readable usernames
    resolved_ids = globus_sdk.IdentityMap(auth_client, list(authentications))

    # put the nested dicts in a format table output can work with
    # while also converting vals into human readable formats
    list_data = [
        {
            "id": key,
            "username": resolved_ids.get(key, {}).get("username"),
            "auth_time": time.strftime(
                "%Y-%m-%d %H:%M %Z", time.localtime(vals["auth_time"])
            ),
        }
        for key, vals in authentications.items()
    ]

    print_command_hint(
        "For information on your primary identity or full identity set see\n"
        "  globus whoami\n"
    )

    display(
        list_data,
        json_converter=lambda x: session_info,
        fields=[("Username", "username"), ("ID", "id"), ("Auth Time", "auth_time")],
    )
