from __future__ import annotations

import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import OMITTABLE_STRING, command
from globus_cli.termio import display

from .._common import INDEX_FIELDS, index_id_arg


@command("update")
@LoginManager.requires_login("search")
@index_id_arg
@click.option(
    "--display-name",
    type=OMITTABLE_STRING,
    default=globus_sdk.MISSING,
    help="A new name for the index.",
)
@click.option(
    "--description",
    type=OMITTABLE_STRING,
    default=globus_sdk.MISSING,
    help="A new description for the index.",
)
def update_command(
    login_manager: LoginManager,
    *,
    index_id: uuid.UUID,
    display_name: str | globus_sdk.MissingType,
    description: str | globus_sdk.MissingType,
) -> None:
    """Update the display name or description of an index."""
    search_client = login_manager.get_search_client()
    display(
        search_client.update_index(
            index_id, display_name=display_name, description=description
        ),
        text_mode=display.RECORD,
        fields=INDEX_FIELDS,
    )
