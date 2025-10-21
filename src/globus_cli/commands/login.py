from __future__ import annotations

import typing as t
import uuid

import click
from click import Context, Parameter
from globus_sdk.scopes import (
    GCSCollectionScopes,
    GCSEndpointScopes,
    SpecificFlowScopes,
    TimersScopes,
)
from globus_sdk.services.flows import SpecificFlowClient

from globus_cli._click_compat import shim_get_metavar
from globus_cli.login_manager import LoginManager, is_client_login
from globus_cli.parsing import command, no_local_server_option
from globus_cli.termio import verbosity

_SHARED_EPILOG = """\

You can check your primary identity with
  globus whoami

For information on which of your identities are in session use
  globus session show

Logout of the Globus CLI with
  globus logout
"""

_LOGIN_EPILOG = (
    (
        """\

You have successfully logged in to the Globus CLI!
"""
    )
    + _SHARED_EPILOG
)

_LOGGED_IN_RESPONSE = (
    (
        """\
You are already logged in!

You may force a new login with
  globus login --force
"""
    )
    + _SHARED_EPILOG
)

_IS_CLIENT_ID_RESPONSE = """\
GLOBUS_CLI_CLIENT_ID and GLOBUS_CLI_CLIENT_SECRET are both set.

When using client credentials, do not run 'globus login'
Clients are always "logged in"
"""


class GCSEndpointType(click.ParamType):
    name = "GCS Server"

    @shim_get_metavar
    def get_metavar(self, param: click.Parameter, ctx: click.Context) -> str:
        return "<endpoint_id>[:<collection_id>]"

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> uuid.UUID | tuple[uuid.UUID, uuid.UUID]:
        if isinstance(value, uuid.UUID):
            return value
        elif isinstance(value, tuple) and len(value) == 2:
            if isinstance(value[0], uuid.UUID) and isinstance(value[1], uuid.UUID):
                return value

        values = value.split(":")
        if len(values) < 1 or len(values) > 2:
            self.fail(
                (
                    "Invalid GCS Specification. Must be supplied in the form "
                    "<endpoint_id>[:<collection_id>]"
                ),
                param,
                ctx,
            )
        try:
            endpoint_id = uuid.UUID(values[0])
        except ValueError:
            self.fail(f"Endpoint ID ({values[0]}) is not a valid UUID", param, ctx)
        try:
            collection_id = uuid.UUID(values[1]) if len(values) == 2 else None
        except ValueError:
            self.fail(f"Collection ID ({values[1]}) is not a valid UUID", param, ctx)

        return endpoint_id if not collection_id else (endpoint_id, collection_id)


class TimerResourceType(click.ParamType):
    name = "TIMER_RESOURCE"

    @shim_get_metavar
    def get_metavar(self, param: click.Parameter, ctx: click.Context) -> str:
        return "flow:<flow_id>"

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> tuple[t.Literal["flow"], uuid.UUID]:
        if not isinstance(value, str):
            self.fail(f"Invalid Timer Resource type: {type(value)}", param, ctx)

        parts = value.split(":")

        if len(parts) == 2 and parts[0] == "flow":
            try:
                return "flow", uuid.UUID(parts[1])
            except ValueError:
                self.fail(f"Flow ID '{parts[1]}' is not a valid UUID", param, ctx)
        else:
            self.fail("Expected a resource in the form 'flow:<flow_id>'", param, ctx)


@command(
    "login",
    short_help="Log into Globus to get credentials for the Globus CLI.",
    disable_options=["format", "map_http_status"],
)
@no_local_server_option
@click.option(
    "--force",
    is_flag=True,
    help="Do a fresh login, ignoring any existing credentials",
)
@click.option(
    "gcs_servers",
    "--gcs",
    type=GCSEndpointType(),
    help=(
        "A GCS Endpoint ID and optional GCS Mapped Collection ID "
        "(<endpoint_id>[:<collection_id>]). For each endpoint, a 'manage_collection' "
        "will be added with a dependent 'data_access' scope if the collection id is"
        "specified"
    ),
    multiple=True,
)
@click.option(
    "flow_ids",
    "--flow",
    type=click.UUID,
    help="""
        A flow ID, for which permissions will be requested.
        This option may be given multiple times.
    """,
    multiple=True,
)
@click.option(
    "timer_targets",
    "--timer",
    type=TimerResourceType(),
    help="A target resource in the form flow:<flow_id>. May be given multiple times.",
    multiple=True,
)
def login_command(
    no_local_server: bool,
    force: bool,
    gcs_servers: tuple[t.Union[uuid.UUID, tuple[uuid.UUID, uuid.UUID]], ...],
    flow_ids: tuple[uuid.UUID, ...],
    timer_targets: tuple[tuple[t.Literal["flow"], uuid.UUID], ...],
) -> None:
    """
    Get credentials for the Globus CLI.

    Necessary before any Globus CLI commands which require authentication will work.

    This command directs you to the page necessary to permit the Globus CLI to make API
    calls for you, and gets the OAuth2 tokens needed to use those permissions.

    The default login method opens your browser to the Globus CLI's authorization
    page, where you can read and consent to the permissions required to use the
    Globus CLI. The CLI then takes care of getting the credentials through a
    local server.

    You can use the GLOBUS_PROFILE environment variable to switch between separate
    accounts without having to log out. If this variable is not set, logging in uses a
    default profile. See the docs for details:

    https://docs.globus.org/cli/environment_variables/#profile_switching_with_globus_profile

    If the CLI detects you are on a remote session, or the --no-local-server option is
    used, the CLI will instead print a link for you to manually follow to the Globus
    CLI's authorization page. After consenting you will then need to copy and paste the
    given access code from the web to the CLI.
    """
    manager = LoginManager()

    if is_client_login():
        raise click.UsageError(_IS_CLIENT_ID_RESPONSE)

    # add GCS servers to LoginManager requirements so that the login check and login
    # flow will make use of the requested GCS servers
    if gcs_servers:
        for gcs_server in gcs_servers:
            if isinstance(gcs_server, uuid.UUID):
                server_id, collection_id = gcs_server, None
            else:
                server_id, collection_id = gcs_server
            rs_name = str(server_id)
            scope = GCSEndpointScopes(rs_name).manage_collections
            if collection_id:
                data_access = GCSCollectionScopes(str(collection_id)).data_access
                scope = scope.with_dependency(data_access)
            manager.add_requirement(rs_name, [scope])

    for flow_id in flow_ids:
        # TODO - evaluate flow authorization requirements dynamically once
        #  `validate_run` has been updated to properly expose session requirements.
        # Rely on the SpecificFlowClient's scope builder.
        flow_scopes = SpecificFlowClient(flow_id).scopes
        assert flow_scopes is not None
        manager.add_requirement(flow_scopes.resource_server, [flow_scopes.user])

    for resource_type, resource_id in timer_targets:
        assert resource_type == "flow"
        flow_scope = SpecificFlowScopes(resource_id).user
        required_scope = TimersScopes.timer.with_dependency(flow_scope)
        manager.add_requirement(TimersScopes.resource_server, [required_scope])

    # if not forcing, stop if user already logged in
    if not force and manager.is_logged_in():
        if verbosity() >= 0:
            click.echo(_LOGGED_IN_RESPONSE)
        return

    manager.run_login_flow(
        no_local_server=no_local_server,
        local_server_message=(
            "You are running 'globus login', which should automatically open "
            "a browser window for you to login.\n"
            "If this fails or you experience difficulty, try "
            "'globus login --no-local-server'"
            "\n---"
        ),
        epilog=_LOGIN_EPILOG,
    )
