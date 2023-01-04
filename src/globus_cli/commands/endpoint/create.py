from __future__ import annotations

import typing as t

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

from ._common import endpoint_create_params, validate_endpoint_create_and_update_params

COMMON_FIELDS = [Field("Message", "message"), Field("Endpoint ID", "id")]

GCP_FIELDS = [Field("Setup Key", "globus_connect_setup_key")]


@command("create", hidden=True)
@endpointish_setattr_params(
    "create",
    entity_types=(
        EntityType.GCSV4_HOST,
        EntityType.GCSV4_SHARE,
        EntityType.GCP_MAPPED,
        EntityType.GCP_GUEST,
    ),
)
@endpoint_create_params
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
)
@mutex_option_group("--shared", "--server", "--personal")
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def endpoint_create(
    *,
    login_manager: LoginManager,
    personal: bool,
    server: bool,
    shared: tuple[str, str] | None,
    **kwargs: t.Any,
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

    # validate options
    kwargs["is_globus_connect"] = personal or None
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
