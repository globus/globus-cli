from __future__ import annotations

import sys
import typing as t
import uuid

from globus_cli.constants import ExplicitNullType
from globus_cli.endpointish import EntityType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    ENDPOINT_PLUS_REQPATH,
    command,
    endpointish_setattr_params,
    mutex_option_group,
    one_use_option,
)
from globus_cli.termio import Field, TextMode, display, print_command_hint
from globus_cli.types import TupleType

from ._common import endpoint_setattr_params, validate_endpoint_create_and_update_params

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

COMMON_FIELDS = [Field("Message", "message"), Field("Endpoint ID", "id")]

GCP_FIELDS = [Field("Setup Key", "globus_connect_setup_key")]


@command("create", hidden=True)
@endpointish_setattr_params(
    "create",
    keyword_style="string",
    verify_style="flag",
)
@endpoint_setattr_params
@one_use_option(
    "--personal",
    is_flag=True,
    help=(
        "Create a Globus Connect Personal endpoint. "
        "Mutually exclusive with --server and --shared."
    ),
)
@one_use_option(
    "--server",
    is_flag=True,
    help=(
        "Create a Globus Connect Server endpoint. "
        "Mutually exclusive with --personal and --shared."
    ),
)
@one_use_option(
    "--shared",
    default=None,
    type=ENDPOINT_PLUS_REQPATH,
    help=(
        "Create a shared endpoint hosted on the given endpoint and path. "
        "Mutually exclusive with --personal and --server."
    ),
    type_annotation=t.Optional[TupleType[uuid.UUID, str]],  # type: ignore[type-arg]
)
@mutex_option_group("--shared", "--server", "--personal")
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def endpoint_create(
    *,
    login_manager: LoginManager,
    personal: bool,
    server: bool,
    shared: tuple[uuid.UUID, str] | None,
    # endpointish setattr params
    display_name: str,
    contact_email: str | None | ExplicitNullType,
    contact_info: str | None | ExplicitNullType,
    default_directory: str | None | ExplicitNullType,
    department: str | None | ExplicitNullType,
    description: str | None | ExplicitNullType,
    disable_verify: bool | None,
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
    oauth_server: str | None,
    organization: str | None | ExplicitNullType,
    preferred_concurrency: int | None,
    preferred_parallelism: int | None,
    public: bool | None,
    subscription_id: uuid.UUID | None,
) -> None:
    """
    WARNING:
    This command is deprecated. Either `globus gcp create` or the Globus Connect Server
    CLI should be used instead.

    Create a new endpoint.

    Requires a display name and exactly one of --personal, --server, or --shared to make
    a Globus Connect Personal, Globus Connect Server, or Shared endpoint respectively.

    Note that `--personal` does not perform local setup steps. When this command is run
    with the `--personal` flag, it returns a setup key which can be passed to
    Globus Connect Personal during setup.
    """
    from globus_cli.services.transfer import assemble_generic_doc, autoactivate

    print_command_hint(
        """\
WARNING: This command is deprecated!

For GCP, use one of the following replacements instead:
    globus gcp create mapped
    globus gcp create guest

For GCS, use the globus-connect-server CLI from your Endpoint."""
    )

    transfer_client = login_manager.get_transfer_client()

    endpoint_type = (
        EntityType.GCP_MAPPED
        if personal
        else EntityType.GCSV4_HOST
        if server
        else EntityType.GCSV4_SHARE
    )

    # build options into a dict for kwarg-expansion
    kwargs = ExplicitNullType.nullify_dict(
        dict(
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
            oauth_server=oauth_server,
            organization=organization,
            preferred_concurrency=preferred_concurrency,
            preferred_parallelism=preferred_parallelism,
            public=public,
            subscription_id=subscription_id,
        )
    )
    kwargs["is_globus_connect"] = personal or None

    # validate options
    validate_endpoint_create_and_update_params(endpoint_type, False, kwargs)

    # shared endpoint creation
    if shared:
        endpoint_id, host_path = shared
        kwargs["host_endpoint"] = endpoint_id
        kwargs["host_path"] = host_path

        ep_doc = assemble_generic_doc("shared_endpoint", **kwargs)
        autoactivate(transfer_client, endpoint_id, if_expires_in=60)
        res = transfer_client.create_shared_endpoint(ep_doc)

    # non shared endpoint creation
    else:
        # omit `is_globus_connect` key if not GCP, otherwise include as `True`
        ep_doc = assemble_generic_doc("endpoint", **kwargs)
        res = transfer_client.create_endpoint(ep_doc)

    # output
    display(
        res,
        fields=(COMMON_FIELDS + GCP_FIELDS if personal else COMMON_FIELDS),
        text_mode=TextMode.text_record,
    )
