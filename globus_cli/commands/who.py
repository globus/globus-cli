import click
import uuid

from globus_cli.safeio import safeprint
from globus_cli.parsing import common_options
from globus_cli.helpers import (
    print_json_response, colon_formatted_print, outformat_is_json, is_verbose)
from globus_cli.services.auth import get_auth_client


@click.command(
    "who", short_help="Resolve a given user ID to a username or vice versa.",
    help=("Resolve a given user ID to a username or vice versa. "
          "Use --verbose to get more user information."))
@common_options
@click.option("--output-id", "output_type", flag_value="id",
              help="Ouput the user's UUID regardless of input type")
@click.option("--output-username", "output_type", flag_value="username",
              help="Ouput the user's username regardless of input type")
@click.argument("uuid_or_username", required=True)
def who_command(uuid_or_username, output_type):
    """
    Executor for `globus get-identities`
    """
    client = get_auth_client()

    # determine if we have a id or username and get_identities with it
    try:
        res = client.get_identities(
            ids=uuid.UUID(uuid_or_username))
        received_id = True
    except ValueError:
        res = client.get_identities(usernames=uuid_or_username)
        received_id = False

    # get the primary identity, or if none exists return an error
    try:
        primary = res["identities"][0]
    except IndexError:
        raise click.ClickException("No identity found with {} {}".format(
            "uuid" if received_id else "username", uuid_or_username))

    # output
    if is_verbose() or outformat_is_json():
        fields = tuple((x, x) for x in
                       ("username", "name", "id", "email", "organization"))
        if outformat_is_json():
            print_json_response(primary)
        else:
            colon_formatted_print(primary, fields)
    else:
        if received_id or output_type == "username":
            safeprint(res["username"])
        else:
            safeprint(primary["id"])
