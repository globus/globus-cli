import base64
import uuid

import click

from globus_cli.parsing import common_options, HiddenOption
from globus_cli.helpers import (
    print_json_response, outformat_is_json, print_table)

from globus_cli.services.auth import get_auth_client


_HIDDEN_TRANSFER_STYLE = 'globus-transfer'


def _b32_decode(v):
    assert v.startswith('u_'), "{0} didn't start with 'u_'".format(v)
    v = v[2:]
    assert len(v) == 26, "u_{0} is the wrong length".format(v)
    # append padding and uppercase so that b32decode will work
    v = v.upper() + (6 * '=')
    return str(uuid.UUID(bytes=base64.b32decode(v)))


@click.command('get-identities',
               help=("Lookup Globus Auth Identities by username and/or UUID."))
@common_options
@click.option('--globus-transfer-decode', 'lookup_style', cls=HiddenOption,
              flag_value=_HIDDEN_TRANSFER_STYLE)
@click.argument('values', required=True, nargs=-1)
def get_identities_command(values, lookup_style):
    """
    Executor for `globus get-identities`
    """
    client = get_auth_client()

    # since get_identites cannot take mixed ids/usernames,
    # we split values into ids and usernames
    ids = []
    usernames = []
    for val in values:
        try:
            uuid.UUID(val)
            ids.append(val)
        except ValueError:
            usernames.append(val)

    # set commandline params if passed
    if lookup_style == _HIDDEN_TRANSFER_STYLE:
        res = client.get_identities(
            ids=','.join(_b32_decode(v) for v in values))

    # make two requests then combine them into one response without duplicates
    else:
        identities_by_id = {}  # dict keyed by ID for preventing duplicates

        if len(ids):
            id_res = client.get_identities(ids=ids)
            for identity in id_res["identities"]:
                identities_by_id[identity["id"]] = identity

        if len(usernames):
            username_res = client.get_identities(usernames=usernames)
            for identity in username_res["identities"]:
                identities_by_id[identity["id"]] = identity

        # convert dict formed from two lists back to one combined list
        res = {"identities":
               [identities_by_id[key] for key in identities_by_id]}

    # json output
    if outformat_is_json():
        print_json_response(res)

    # text output is a table made out of response data
    else:
        print_table(res["identities"],
                    [('ID', 'id'), ('Username', 'username'),
                     ('Full Name', 'name'), ('Organization', 'organization'),
                     ('Email Address', 'email')])
