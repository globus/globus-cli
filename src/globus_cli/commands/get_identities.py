import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import IdentityType, command
from globus_cli.termio import FORMAT_TEXT_TABLE, Field, formatted_print, is_verbose
from globus_cli.utils import CLIStubResponse


@command(
    "get-identities",
    short_help="Lookup Globus Auth Identities",
    adoc_examples="""Resolve a user ID (outputs the user's username)

[source,bash]
----
$ globus get-identities c699d42e-d274-11e5-bf75-1fc5bf53bb24
----

Resolve a username (outputs the user's ID)

[source,bash]
----
$ globus get-identities go@globusid.org
----

Resolve multiple usernames and or IDs with tabular output

[source,bash]
----
$ globus get-identities --verbose go@globusid.org clitester1a@globusid.org \
84942ca8-17c4-4080-9036-2f58e0093869
----
""",
)
@click.argument(
    "values", type=IdentityType(allow_b32_usernames=True), required=True, nargs=-1
)
@click.option("--provision", hidden=True, is_flag=True)
@LoginManager.requires_login(LoginManager.AUTH_RS)
def get_identities_command(*, login_manager: LoginManager, values, provision):
    """
    Lookup Globus Auth Identities given one or more uuids
    and/or usernames.

    Default output resolves each UUID to a username and each username to a UUID,
    with one output per line in the same order as the inputs.
    If a particular input had no corresponding identity in Globus Auth,
    "NO_SUCH_IDENTITY" is printed instead.

    If more fields are desired, --verbose will give tabular output, but does not
    guarantee order and ignores inputs with no corresponding Globus Auth identity.
    """
    auth_client = login_manager.get_auth_client()

    # since API doesn't accept mixed ids and usernames,
    # split input values into separate lists
    ids = [v.value for v in values if v.idtype == "identity"]
    usernames = [v.value for v in values if v.idtype == "username"]

    # make two calls to get_identities with ids and usernames
    # then combine the calls into one response
    results = []
    if len(ids):
        results += auth_client.get_identities(ids=ids, provision=provision)[
            "identities"
        ]
    if len(usernames):
        results += auth_client.get_identities(usernames=usernames, provision=provision)[
            "identities"
        ]
    res = CLIStubResponse({"identities": results})

    def _custom_text_format(identities):
        """
        Non-verbose text output is customized
        """

        def resolve_identity(value):
            """
            helper to deal with variable inputs and uncertain response order
            """
            for identity in identities:
                if identity["id"] == value:
                    return identity["username"]
                if identity["username"] == value:
                    return identity["id"]
            return "NO_SUCH_IDENTITY"

        # standard output is one resolved identity per line in the same order
        # as the inputs. A resolved identity is either a username if given a
        # UUID vice versa, or "NO_SUCH_IDENTITY" if the identity could not be
        # found
        for val in values:
            click.echo(resolve_identity(val.value))

    formatted_print(
        res,
        response_key="identities",
        fields=[
            Field("ID", "id"),
            Field("Username", "username"),
            Field("Full Name", "name"),
            Field("Organization", "organization"),
            Field("Email Address", "email"),
        ],
        # verbose output is a table. Order not guaranteed, may contain
        # duplicates
        text_format=(FORMAT_TEXT_TABLE if is_verbose() else _custom_text_format),
    )
