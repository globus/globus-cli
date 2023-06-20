from __future__ import annotations

import click

from globus_cli.constants import ExplicitNullType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpointish_params
from globus_cli.termio import Field, TextMode, display

from ._common import deprecated_verify_option


@command("mapped", short_help="Create a new GCP Mapped Collection")
@endpointish_params.create(name="collection", keyword_style="string")
@click.option(
    "--subscription-id",
    help="Set the collection as managed with the given subscription ID",
)
@click.option("--public", is_flag=True, help="Set the collection to be public.")
@deprecated_verify_option
@LoginManager.requires_login("transfer")
def mapped_command(
    *,
    login_manager: LoginManager,
    display_name: str,
    description: str | None | ExplicitNullType,
    info_link: str | None | ExplicitNullType,
    contact_info: str | None | ExplicitNullType,
    contact_email: str | None | ExplicitNullType,
    organization: str | None | ExplicitNullType,
    department: str | None | ExplicitNullType,
    keywords: str | None,
    default_directory: str | None | ExplicitNullType,
    force_encryption: bool | None,
    verify: dict[str, bool],
    subscription_id: str | None,
    disable_verify: bool | None,
    user_message: str | None | ExplicitNullType,
    user_message_link: str | None | ExplicitNullType,
    public: bool,
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

    if disable_verify is not None:
        verify["disable_verify"] = disable_verify

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
        subscription_id=subscription_id,
        public=public,
        user_message=user_message,
        user_message_link=user_message_link,
        **verify,
    )

    res = transfer_client.create_endpoint(ep_doc)

    # output
    display(
        res,
        fields=[
            Field("Message", "message"),
            Field("Collection ID", "id"),
            Field("Setup Key", "globus_connect_setup_key"),
        ],
        text_mode=TextMode.text_record,
    )
