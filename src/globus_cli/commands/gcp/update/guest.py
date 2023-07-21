from __future__ import annotations

import uuid

from globus_cli.constants import ExplicitNullType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import collection_id_arg, command, endpointish_params
from globus_cli.termio import TextMode, display


@command("guest", short_help="Update a Guest Collection on GCP")
@collection_id_arg
@endpointish_params.update(
    name="collection",
    keyword_style="string",
    skip=("user_message", "user_message_link"),
)
@LoginManager.requires_login("transfer")
def guest_command(
    login_manager: LoginManager,
    *,
    collection_id: uuid.UUID,
    display_name: str | None,
    contact_email: str | None | ExplicitNullType,
    contact_info: str | None | ExplicitNullType,
    default_directory: str | None | ExplicitNullType,
    department: str | None | ExplicitNullType,
    description: str | None | ExplicitNullType,
    force_encryption: bool | None,
    info_link: str | None | ExplicitNullType,
    keywords: str | None,
    organization: str | None | ExplicitNullType,
    verify: dict[str, bool],
) -> None:
    """
    Update a Guest Collection on a Globus Connect Personal Mapped Collection
    """
    from globus_cli.services.transfer import assemble_generic_doc

    transfer_client = login_manager.get_transfer_client()

    # build the endpoint document to submit
    ep_doc = assemble_generic_doc(
        "endpoint",
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
        **verify,
    )

    # make the update
    res = transfer_client.update_endpoint(collection_id, ep_doc)
    display(res, text_mode=TextMode.text_raw, response_key="message")
