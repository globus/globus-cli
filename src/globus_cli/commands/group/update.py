from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display

from ._common import group_id_arg


@command("update")
@group_id_arg
@click.option("--name", help="Name for the group")
@click.option("--description", help="Description for the group")
@click.option(
    "--terms-and-conditions", help="Terms and conditions for group membership"
)
@LoginManager.requires_login("groups")
def group_update(
    login_manager: LoginManager,
    *,
    group_id: uuid.UUID,
    name: str | None,
    description: str | None,
    terms_and_conditions: str | None,
) -> None:
    """Update an existing group."""
    groups_client = login_manager.get_groups_client()

    # get the current state of the group
    group = groups_client.get_group(group_id)

    # assemble put data using existing values for any field not given
    # note that the API only allows modification of certain fields
    #   https://groups.api.globus.org/redoc#tag/groups/operation/update_group_v2_groups__group_id__put
    data = {}
    for attrname, argval in (
        ("name", name),
        ("description", description),
        ("terms_and_conditions", terms_and_conditions),
    ):
        if argval is not None:
            data[attrname] = argval
        else:
            data[attrname] = group[attrname]

    response = groups_client.update_group(group_id, data)

    display(response, simple_text="Group updated successfully")
