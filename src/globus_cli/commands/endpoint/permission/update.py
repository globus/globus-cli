from __future__ import annotations

import typing as t
import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import display

from ._common import expiration_date_option


@command(
    "update",
    short_help="Update an access control rule.",
    adoc_examples="""Change existing access control rule to read only:

[source,bash]
----
$ ep_id=aa752cea-8222-5bc8-acd9-555b090c0ccb
$ rule_id=1ddeddda-1ae8-11e7-bbe4-22000b9a448b
$ globus endpoint permission update $ep_id $rule_id --permissions r
----
""",
)
@endpoint_id_arg
@click.argument("rule_id")
@click.option(
    "--permissions",
    type=click.Choice(("r", "rw"), case_sensitive=False),
    help="Permissions to add. Read-Only or Read/Write",
)
@expiration_date_option
@LoginManager.requires_login("transfer")
def update_command(
    login_manager: LoginManager,
    *,
    permissions: t.Literal["r", "rw"] | None,
    rule_id: str,
    endpoint_id: uuid.UUID,
    expiration_date: str | None,
) -> None:
    """
    Update an existing access control rule's permissions.

    The --permissions option is required, as it is currently the only field
    that can be updated.
    """
    from globus_cli.services.transfer import assemble_generic_doc

    transfer_client = login_manager.get_transfer_client()

    rule_data = assemble_generic_doc(
        "access", permissions=permissions, expiration_date=expiration_date
    )
    res = transfer_client.update_endpoint_acl_rule(endpoint_id, rule_id, rule_data)
    display(res, text_mode=display.RAW, response_key="message")
