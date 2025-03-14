from __future__ import annotations

import click

from globus_cli.endpointish import WrongEntityTypeError

from ..registry import error_handler


@error_handler(error_class=WrongEntityTypeError, exit_status=3)
def wrong_endpoint_type_error_hook(exception: WrongEntityTypeError) -> None:
    msg = exception.expected_message + "\n" + exception.actual_message + "\n\n"
    click.secho(msg, fg="yellow", err=True)

    should_use = exception.should_use_command()
    if should_use:
        click.echo(
            "Please run the following command instead:\n\n"
            f"    {should_use} {exception.endpoint_id}\n",
            err=True,
        )
    else:
        msg = "This operation is not supported on objects of this type."
        click.secho(msg, fg="red", bold=True, err=True)
