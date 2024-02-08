import uuid

import click
from globus_sdk.paging import Paginator

from globus_cli.commands.gcs.endpoint.role._common import role_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import display
from globus_cli.utils import PagingWrapper


@command("list")
@endpoint_id_arg
@click.option(
    "--all-roles", is_flag=True, help="Show all roles, not just yours.", default=False
)
@LoginManager.requires_login("transfer")
def list_command(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    all_roles: bool,
) -> None:
    """List all roles on a GCS Endpoint associated with you."""
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    auth_client = login_manager.get_auth_client()

    paginator = Paginator.wrap(gcs_client.get_role_list)
    paginated_call = paginator(include="all_roles") if all_roles else paginator()
    paging_wrapper = PagingWrapper(paginated_call.items(), json_conversion_key="DATA")

    display(
        paging_wrapper,
        fields=role_fields(auth_client),
        json_converter=paging_wrapper.json_converter,
    )
