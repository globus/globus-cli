from __future__ import annotations

import typing as t
import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import display


@command(
    "is-activated",
    short_help="Check if an endpoint is activated",
    adoc_exit_status="""0 if the endpoint is activated.

1 if the endpoint is not activated, unless --map-http-status has been
used to change exit behavior on http error codes.

2 if the command was used improperly.
""",
    adoc_examples=r"""[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint is-activated $ep_id
----

Check *globus endpoint is-activated* as part of a script:

[source,bash]
----
ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
globus endpoint is-activated $ep_id
if [ $? -ne 0 ]; then
    echo "$ep_id is not activated! This script cannot run!"
    exit 1
fi
# ... more stuff using $ep_id below ...
----

Use `is-activated` to get and parse activation requirements, finding out the
expiration time, but only for endpoints which are activated. Uses '--jmespath'
to select fields, exit status to indicate that the endpoint is or is not
activated, and '--format=UNIX' to get nice, unix-friendly output.

[source,bash]
----
ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
output="$(globus endpoint is-activated "$ep_id" \
    --jmespath expires_in --format unix)"
if [ $? -eq 0 ]; then
    if [ "$output" -eq "-1" ]; then
        echo "$ep_id is activated forever. Activation never expires."
    else
        echo "$ep_id activation expires in $output seconds"
    fi
else
    echo "$ep_id not activated"
    exit 1
fi
----
""",
)
@endpoint_id_arg
@click.option(
    "--until",
    type=int,
    help=(
        "An integer number of seconds in the future. If the "
        "endpoint is activated, but will expire by then, exits "
        "with status 1"
    ),
)
@click.option(
    "--absolute-time",
    is_flag=True,
    show_default=True,
    default=False,
    help=(
        "Treat the value of --until as a POSIX timestamp (seconds "
        "since Epoch), not a number of seconds into the future."
    ),
)
@LoginManager.requires_login("transfer")
def endpoint_is_activated(
    *,
    login_manager: LoginManager,
    endpoint_id: uuid.UUID,
    until: int | None,
    absolute_time: bool,
) -> None:
    """
    Check if an endpoint is activated or requires activation.

    If it requires activation, exits with status 1, otherwise exits with status 0.

    If the endpoint is not activated, this command will output a link for web
    activation, or you can use 'globus endpoint activate' to activate the endpoint.
    """
    from globus_cli.services.transfer import activation_requirements_help_text

    transfer_client = login_manager.get_transfer_client()
    res = transfer_client.endpoint_get_activation_requirements(endpoint_id)

    def fail(deadline: int | None = None) -> t.NoReturn:
        exp_string = ""
        if deadline is not None:
            exp_string = f" or will expire within {deadline} seconds"
        requirements_help = activation_requirements_help_text(res, endpoint_id)

        message = (
            f"'{endpoint_id}' is not activated{exp_string}.\n\n{requirements_help}"
        )
        display(res, simple_text=message)
        click.get_current_context().exit(1)

    def success(msg: str) -> t.NoReturn:
        display(res, simple_text=msg)
        click.get_current_context().exit(0)

    # eternally active endpoints have a special expires_in value
    if res["expires_in"] == -1:
        success(f"'{endpoint_id}' does not require activation")

    # autoactivation is not supported and --until was not passed
    if until is None:
        # and we are active right now (0s in the future)...
        if res.active_until(0):
            success(f"'{endpoint_id}' is activated")
        # or we are not active
        fail()

    # autoactivation is not supported and --until was passed
    if res.active_until(until, relative_time=not absolute_time):
        success(f"'{endpoint_id}' will be active for at least {until} seconds")
    else:
        fail(deadline=until)
