import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import formatted_print


@command("delete")
@LoginManager.requires_login(LoginManager.SEARCH_RS)
@click.argument("INDEX_ID")
def delete_command(*, login_manager: LoginManager, index_id: str):
    """(BETA) Delete a Search Index"""
    search_client = login_manager.get_search_client()
    formatted_print(
        search_client.delete(f"/beta/index/{index_id}"),
        simple_text=f"Index {index_id} is now marked for deletion.\n"
        "It will be fully deleted after cleanup steps complete.",
    )
