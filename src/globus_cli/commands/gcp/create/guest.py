from __future__ import annotations

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    ENDPOINT_PLUS_REQPATH,
    command,
    endpointish_create_and_update_params,
)
from globus_cli.termio import FORMAT_TEXT_RECORD, formatted_print


@command("guest", short_help="Create a new Guest Collection on GCP")
@endpointish_create_and_update_params("create", "collection")
@click.argument("HOST_GCP_PATH", type=ENDPOINT_PLUS_REQPATH)
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def guest_command(
    *,
    login_manager: LoginManager,
    display_name: str,
    host_gcp_path: tuple[str, str],
    description: str | None,
    info_link: str | None,
    contact_info: str | None,
    contact_email: str | None,
    organization: str | None,
    department: str | None,
    keywords: str | None,
    default_directory: str | None,
    force_encryption: bool | None,
    disable_verify: bool | None,
) -> None:
    """
    Create a new Guest Collection on a Globus Connect Personal Endpoint

    The host ID and a path to the root for the Guest Collection are required.
    """
    from globus_cli.services.transfer import assemble_generic_doc, autoactivate

    transfer_client = login_manager.get_transfer_client()

    # build the endpoint document to submit
    host_endpoint_id, host_path = host_gcp_path
    ep_doc = assemble_generic_doc(
        "shared_endpoint",
        host_endpoint=host_endpoint_id,
        host_path=host_path,
        display_name=display_name,
        description=description,
        info_link=info_link,
        contact_info=contact_info,
        contact_email=contact_email,
        organization=organization,
        department=department,
        keywords=keywords,
        default_directory=default_directory,
        force_encryption=force_encryption,
        disable_verify=disable_verify,
    )

    autoactivate(transfer_client, host_endpoint_id, if_expires_in=60)
    res = transfer_client.create_shared_endpoint(ep_doc)

    # output
    formatted_print(
        res,
        fields=[("Message", "message"), ("Collection ID", "id")],
        text_format=FORMAT_TEXT_RECORD,
    )
