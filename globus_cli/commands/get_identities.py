import base64
import uuid
import click

from globus_sdk import GlobusResponse

from globus_cli.safeio import safeprint, formatted_print, FORMAT_TEXT_TABLE
from globus_cli.parsing import common_options, HiddenOption
from globus_cli.helpers import is_verbose

from globus_cli.services.auth import get_auth_client


_HIDDEN_TRANSFER_STYLE = "globus-transfer"


def _b32_decode(v):
    assert v.startswith("u_"), "{0} didn't start with 'u_'".format(v)
    v = v[2:]
    assert len(v) == 26, "u_{0} is the wrong length".format(v)
    # append padding and uppercase so that b32decode will work
    v = v.upper() + (6 * "=")
    return str(uuid.UUID(bytes=base64.b32decode(v)))


@click.command("get-identities", short_help="Lookup Globus Auth Identities",
               help="Lookup Globus Auth Identities given one or more uuids "
               "and/or usernames. Either resolves each uuid to a username and "
               "vice versa, or use --verbose for tabular output.")
@common_options
@click.option("--globus-transfer-decode", "lookup_style", cls=HiddenOption,
              flag_value=_HIDDEN_TRANSFER_STYLE)
@click.argument("values", required=True, nargs=-1)
def get_identities_command(values, lookup_style):
    """
    Executor for `globus get-identities`
    """
    client = get_auth_client()

    # set commandline params if passed
    if lookup_style == _HIDDEN_TRANSFER_STYLE:
        res = client.get_identities(
            ids=",".join(_b32_decode(v) for v in values))

    else:
        # since API doesn't accept mixed ids and usernames,
        # split input values into separate lists
        ids = []
        usernames = []
        for val in values:
            try:
                uuid.UUID(val)
                ids.append(val)
            except ValueError:
                usernames.append(val)

        # make two calls to get_identities with ids and usernames
        # then combine the calls into one response
        results = []
        if len(ids):
            results += client.get_identities(ids=ids)["identities"]
        if len(usernames):
            results += client.get_identities(usernames=usernames)["identities"]
        res = GlobusResponse({"identities": results})

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
            safeprint(resolve_identity(val))

    formatted_print(
        res, response_key='identities',
        fields=[('ID', 'id'), ('Username', 'username'),
                ('Full Name', 'name'), ('Organization', 'organization'),
                ('Email Address', 'email')],
        # verbose output is a table. Order not guaranteed, may contain
        # duplicates
        text_format=(FORMAT_TEXT_TABLE
                     if is_verbose() else
                     _custom_text_format))
