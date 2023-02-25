from textwrap import dedent

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import TextMode, display


def _spec_to_matches(server_list, server_spec, mode):
    """
    mode is in {uri, hostname, hostname_port}

    A list of matching server docs.
    Should usually be 0 or 1 matches. Multiple matches are possible though.
    """
    assert mode in ("uri", "hostname", "hostname_port")

    def match(server_doc):
        if mode == "hostname":
            return server_spec == server_doc["hostname"]
        elif mode == "hostname_port":
            return server_spec == "{}:{}".format(
                server_doc["hostname"], server_doc["port"]
            )
        elif mode == "uri":
            return server_spec == "{}://{}:{}".format(
                server_doc["scheme"], server_doc["hostname"], server_doc["port"]
            )
        else:
            raise NotImplementedError("Unreachable error! Something is very wrong.")

    return [server_doc for server_doc in server_list if match(server_doc)]


def _detect_mode(server):
    try:
        int(server)
        return "id"
    except ValueError:
        pass

    if "://" in server:
        return "uri"

    if ":" in server:
        return "hostname_port"

    return "hostname"


@command(
    "delete",
    short_help="Delete a server belonging to an endpoint",
    adoc_examples="""[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ server_id=294682
$ globus endpoint server delete $ep_id $server_id
----
""",
)
@endpoint_id_arg
@click.argument("server")
@LoginManager.requires_login("transfer")
def server_delete(*, login_manager: LoginManager, endpoint_id, server):
    """
    Delete a server belonging to an endpoint.

    SERVER may be a server ID, HOSTNAME, HOSTNAME:PORT, or URI
    (`SCHEME://HOSTNAME:PORT`)

    To get the IDs of servers to remove use 'globus endpoint server list'.
    """
    transfer_client = login_manager.get_transfer_client()

    mode = _detect_mode(server)

    # list (even if not necessary) in order to make errors more consistent when
    # mode='id'
    endpoint, server_list = transfer_client.get_endpoint_w_server_list(endpoint_id)

    if server_list == "S3":
        raise click.UsageError("You cannot delete servers from S3 endpoints.")

    # we don't *have to* raise an error in the GCP case, since the API would
    # deny it too, but doing so makes our errors a little bit more consistent
    # with deletes against S3 endpoints and shares
    if endpoint["is_globus_connect"]:
        raise click.UsageError(
            "You cannot delete servers from Globus Connect Personal endpoints"
        )

    if mode != "id":
        matches = _spec_to_matches(server_list, server, mode)
        if not matches:
            raise click.UsageError(f'No server was found matching "{server}"')
        elif len(matches) > 1:
            raise click.UsageError(
                dedent(
                    """\
                Multiple servers matched "{}":
                    {}
            """
                ).format(server, [x["id"] for x in matches])
            )
        else:
            server = matches[0]["id"]

    response = transfer_client.delete_endpoint_server(endpoint_id, server)

    display(response, text_mode=TextMode.text_raw, response_key="message")
