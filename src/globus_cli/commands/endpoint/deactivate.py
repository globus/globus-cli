import uuid

import click

from globus_cli.parsing import command, endpoint_id_arg


@command("deactivate", deprecated=True, hidden=True)
@endpoint_id_arg
def endpoint_deactivate(*, endpoint_id: uuid.UUID) -> None:
    """
    Deactivate an endpoint.


    Endpoint Activation has been removed from the Globus ecosystem. This command
    no longer does anything.
    """
    click.echo(
        click.style(
            "`globus endpoint deactivate` has been deprecated and "
            "will be removed in a future release.",
            fg="yellow",
        ),
        err=True,
    )
