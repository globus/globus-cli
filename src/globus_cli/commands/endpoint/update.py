from __future__ import annotations

import sys
import uuid

import click

from globus_cli.constants import ExplicitNullType
from globus_cli.endpointish import Endpointish
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    command,
    endpoint_id_arg,
    endpointish_params,
    mutex_option_group,
)
from globus_cli.termio import TextMode, display

from ._common import validate_endpoint_create_and_update_params

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal


@command("update")
@endpoint_id_arg
@endpointish_params.update(name="endpoint", keyword_style="string", verify_style="flag")
@endpointish_params.legacy_transfer_params()
@click.option(
    "--no-default-directory",
    is_flag=True,
    flag_value=True,
    default=None,
    help="Unset any default directory on the endpoint",
)
@mutex_option_group("--default-directory", "--no-default-directory")
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def endpoint_update(
    *,
    login_manager: LoginManager,
    endpoint_id: uuid.UUID,
    contact_email: str | None | ExplicitNullType,
    contact_info: str | None | ExplicitNullType,
    default_directory: str | None | ExplicitNullType,
    department: str | None | ExplicitNullType,
    description: str | None | ExplicitNullType,
    disable_verify: bool | None,
    display_name: str | None,
    force_encryption: bool | None,
    info_link: str | None | ExplicitNullType,
    keywords: str | None,
    location: tuple[float, float] | None,
    managed: bool | None,
    max_concurrency: int | None,
    max_parallelism: int | None,
    myproxy_dn: str | None,
    myproxy_server: str | None,
    network_use: Literal["normal", "minimal", "aggressive", "custom"] | None,
    no_default_directory: bool | None,
    oauth_server: str | None,
    organization: str | None | ExplicitNullType,
    preferred_concurrency: int | None,
    preferred_parallelism: int | None,
    public: bool | None,
    subscription_id: uuid.UUID | None,
) -> None:
    """Update attributes of an endpoint"""
    from globus_cli.services.transfer import assemble_generic_doc

    transfer_client = login_manager.get_transfer_client()

    epish = Endpointish(endpoint_id, transfer_client=transfer_client)
    epish.assert_is_traditional_endpoint()

    ep_doc = assemble_generic_doc(
        "endpoint",
        contact_email=contact_email,
        contact_info=contact_info,
        default_directory=default_directory,
        department=department,
        description=description,
        disable_verify=disable_verify,
        display_name=display_name,
        force_encryption=force_encryption,
        info_link=info_link,
        keywords=keywords,
        location=location,
        managed=managed,
        max_concurrency=max_concurrency,
        max_parallelism=max_parallelism,
        myproxy_dn=myproxy_dn,
        myproxy_server=myproxy_server,
        network_use=network_use,
        no_default_directory=no_default_directory,
        oauth_server=oauth_server,
        organization=organization,
        preferred_concurrency=preferred_concurrency,
        preferred_parallelism=preferred_parallelism,
        public=public,
        subscription_id=subscription_id,
    )

    validate_endpoint_create_and_update_params(
        epish.entity_type, epish.is_managed, ep_doc
    )

    # make the update
    res = transfer_client.update_endpoint(endpoint_id, ep_doc)
    display(res, text_mode=TextMode.text_raw, response_key="message")
