import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import FORMAT_TEXT_TABLE, Field, formatted_print

from ..._common import index_id_arg, resolved_principals_field


@command("list")
@index_id_arg
@LoginManager.requires_login(LoginManager.SEARCH_RS, LoginManager.AUTH_RS)
def list_command(*, login_manager: LoginManager, index_id: uuid.UUID):
    """List roles on an index (requires admin)"""
    search_client = login_manager.get_search_client()
    auth_client = login_manager.get_auth_client()

    res = search_client.get_role_list(index_id)
    formatted_print(
        res,
        fields=[
            Field("ID", "id"),
            Field("Role", "role_name"),
            resolved_principals_field(auth_client, res["role_list"]),
        ],
        text_format=FORMAT_TEXT_TABLE,
        response_key="role_list",
    )
