import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import TextMode, display

from .._common import INDEX_FIELDS


@command("create")
@LoginManager.requires_login("search")
@click.argument("DISPLAY_NAME")
@click.argument("DESCRIPTION")
def create_command(
    *, login_manager: LoginManager, display_name: str, description: str
) -> None:
    """(BETA) Create a new Index"""
    index_doc = {"display_name": display_name, "description": description}
    search_client = login_manager.get_search_client()
    display(
        search_client.post("/beta/index", data=index_doc),
        text_mode=TextMode.text_record,
        fields=INDEX_FIELDS,
    )
