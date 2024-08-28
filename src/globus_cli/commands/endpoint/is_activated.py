from __future__ import annotations

import uuid

import click

from globus_cli.parsing import command, endpoint_id_arg


@command("is-activated", deprecated=True, hidden=True)
@endpoint_id_arg
@click.option("--until", type=int)
@click.option("--absolute-time", is_flag=True, show_default=True, default=False)
def endpoint_is_activated(
    *,
    endpoint_id: uuid.UUID,
    until: int | None,
    absolute_time: bool,
) -> None:
    """
    Check if an endpoint is activated or requires activation.

    Endpoint Activation has been removed from the Globus ecosystem. This command
    no longer does anything.
    """
    click.echo(
        click.style(
            "`globus endpoint is-activated` has been deprecated and "
            "will be removed in a future release.",
            fg="yellow",
        ),
        err=True,
    )
