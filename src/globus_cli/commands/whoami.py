import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, TextMode, display, is_verbose, print_command_hint


@command(
    "whoami",
    disable_options=["map_http_status"],
    short_help="Show the currently logged-in identity",
    adoc_output="""\
Note: this output is not affected by sessions in any way. For information
on which of your identities are in session use *globus session show*

If no options are given the default output is just the preferred
username of the logged in identity.

If *--linked-identities* is given the output will be each username in the
logged-in user's identity set.

If *--verbose* is given, the following fields will be output, either in
a record format or a table format if *--linked-identities* is also given.

- 'Username'
- 'Name'
- 'ID'
- 'Email'
""",
    adoc_examples="""Display multiple fields of the current user's information:

[source,bash]
----
$ globus whoami -v
----

Display each username in the current user's identity set:

[source,bash]
----
$ globus whoami --linked-identities
----
""",
)
@click.option(
    "--linked-identities",
    is_flag=True,
    help="Also show identities linked to the currently logged-in primary identity.",
)
@LoginManager.requires_login(LoginManager.AUTH_RS)
def whoami_command(*, login_manager: LoginManager, linked_identities: bool):
    """
    Display information for the currently logged-in user.
    """
    auth_client = login_manager.get_auth_client()

    # get userinfo from auth.
    # if we get back an error the user likely needs to log in again
    try:
        res = auth_client.oauth2_userinfo()
    except globus_sdk.AuthAPIError:
        click.echo(
            "Unable to get user information. Please try logging in again.", err=True
        )
        click.get_current_context().exit(1)

    print_command_hint(
        "For information on which identities are in session see\n"
        "  globus session show\n"
    )

    # --linked-identities either displays all usernames or a table if verbose
    if linked_identities:
        try:
            display(
                res["identity_set"],
                fields=[
                    Field("Username", "username"),
                    Field("Name", "name"),
                    Field("ID", "sub"),
                    Field("Email", "email"),
                ],
                simple_text=(
                    None
                    if is_verbose()
                    else "\n".join([x["username"] for x in res["identity_set"]])
                ),
            )
        except KeyError:
            click.echo(
                "Your current login does not have the consents required "
                "to view your full identity set. Please log in again "
                "to agree to the required consents.",
                err=True,
            )

    # Default output is the top level data
    else:
        display(
            res,
            text_mode=TextMode.text_record,
            fields=[
                Field("Username", "preferred_username"),
                Field("Name", "name"),
                Field("ID", "sub"),
                Field("Email", "email"),
            ],
            simple_text=(None if is_verbose() else res["preferred_username"]),
        )
