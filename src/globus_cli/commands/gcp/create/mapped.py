from __future__ import annotations

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpointish_create_and_update_params
from globus_cli.termio import FORMAT_TEXT_RECORD, Field, formatted_print


@command("mapped", short_help="Create a new GCP Mapped Collection")
@endpointish_create_and_update_params("create", "collection")
@click.option(
    "--subscription-id",
    help="Set the endpoint as a managed endpoint with the given subscription ID",
)
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def mapped_command(
    *,
    login_manager: LoginManager,
    display_name: str,
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
    subscription_id: str | None,
) -> None:
    """
    Create a new Globus Connect Personal Mapped Collection.

    In GCP, the Mapped Collection and Endpoint are synonymous.

    NOTE: This command does not install or start a local installation of Globus Connect
    Personal. It performs the registration step with the Globus service and prints out a
    setup-key which can be used to configure an installed Globus Connect Personal to use
    that registration.
    """
    from globus_cli.services.transfer import assemble_generic_doc

    transfer_client = login_manager.get_transfer_client()

    # build the endpoint document to submit
    ep_doc = assemble_generic_doc(
        "endpoint",
        is_globus_connect=True,
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
        subscription_id=subscription_id,
    )

    res = transfer_client.create_endpoint(ep_doc)

    # output
    formatted_print(
        res,
        fields=[
            Field("Message", "message"),
            Field("Collection ID", "id"),
            Field("Setup Key", "globus_connect_setup_key"),
        ],
        text_format=FORMAT_TEXT_RECORD,
    )
