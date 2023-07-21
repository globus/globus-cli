from __future__ import annotations

import uuid

import click

from globus_cli.constants import ExplicitNullType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import collection_id_arg, command, endpointish_params
from globus_cli.termio import TextMode, display


@command("mapped", short_help="Update a GCP Mapped Collection")
@collection_id_arg
@endpointish_params.update(name="collection", keyword_style="string")
@click.option(
    "--subscription-id",
    help="Set the collection as managed with the given subscription ID",
)
@click.option(
    "--public/--private",
    default=None,
    is_flag=True,
    help="Set the collection to be public or private.",
)
@LoginManager.requires_login("transfer")
def mapped_command(
    login_manager: LoginManager,
    *,
    collection_id: uuid.UUID,
    display_name: str | None,
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
    user_message: str | None | ExplicitNullType,
    user_message_link: str | None | ExplicitNullType,
    public: bool | None,
) -> None:
    """
    Update a Globus Connect Personal Mapped Collection.

    In GCP, the Mapped Collection and Endpoint are synonymous.
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
        subscription_id=subscription_id,
        public=public,
        user_message=user_message,
        user_message_link=user_message_link,
        **verify,
    )

    # make the update
    res = transfer_client.update_endpoint(collection_id, ep_doc)
    display(res, text_mode=TextMode.text_raw, response_key="message")
