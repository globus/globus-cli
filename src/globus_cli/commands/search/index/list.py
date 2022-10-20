from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import FORMAT_TEXT_TABLE, Field, formatted_print

from .._common import INDEX_FIELDS

INDEX_LIST_FIELDS = INDEX_FIELDS + [
    Field("Permissions", lambda x: ",".join(x["permissions"])),
]


@command("list")
@LoginManager.requires_login(LoginManager.SEARCH_RS)
def list_command(*, login_manager: LoginManager):
    """List indices where you have some permissions"""
    search_client = login_manager.get_search_client()
    formatted_print(
        search_client.get("/v1/index_list"),
        fields=INDEX_LIST_FIELDS,
        text_format=FORMAT_TEXT_TABLE,
        response_key="index_list",
    )
