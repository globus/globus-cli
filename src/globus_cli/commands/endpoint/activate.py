from __future__ import annotations

import uuid

import click

from globus_cli.parsing import command, endpoint_id_arg, mutex_option_group


@command("activate", deprecated=True, hidden=True)
@endpoint_id_arg
@click.option("--web", is_flag=True, default=False)
@click.option("--no-browser", is_flag=True, default=False)
@click.option("--myproxy", is_flag=True, default=False)
@click.option("--myproxy-username", "-U")
@click.option("--myproxy-password", "-P", hidden=True)
@click.option("--myproxy-lifetime", type=int)
@click.option("--no-autoactivate", is_flag=True, default=False)
@click.option("--force", is_flag=True, default=False)
@mutex_option_group("--web", "--myproxy")
def endpoint_activate(
    *,
    endpoint_id: uuid.UUID,
    myproxy: bool,
    myproxy_username: str | None,
    myproxy_password: str | None,
    myproxy_lifetime: int | None,
    web: bool,
    no_browser: bool,
    no_autoactivate: bool,
    force: bool,
) -> None:
    """
    Activate an endpoint.

    Endpoint Activation has been removed from the Globus ecosystem. This command
    no longer does anything.
    """
    click.echo(
        click.style(
            "`globus endpoint activate` has been deprecated and "
            "will be removed in a future release.",
            fg="yellow",
        ),
        err=True,
    )
