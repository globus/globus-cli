from __future__ import annotations

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display


@command("create")
@click.argument("name")
@click.option("--description", help="Description for the group")
@LoginManager.requires_login("groups")
def group_create(
    *, login_manager: LoginManager, name: str, description: str | None
) -> None:
    """Create a new group"""
    groups_client = login_manager.get_groups_client()

    response = groups_client.create_group(
        {
            "name": name,
            "description": description,
        }
    )
    group_id = response["id"]

    display(response, simple_text=f"Group {group_id} created successfully")
