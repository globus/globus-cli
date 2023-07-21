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
    login_manager: LoginManager, *, display_name: str, description: str
) -> None:
    """Create a new Index"""
    search_client = login_manager.get_search_client()
    display(
        search_client.create_index(display_name=display_name, description=description),
        text_mode=TextMode.text_record,
        fields=INDEX_FIELDS,
    )
