from __future__ import annotations

import typing as t

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    ENDPOINT_PLUS_REQPATH,
    command,
    endpointish_create_and_update_params,
    mutex_option_group,
    one_use_option,
)
from globus_cli.termio import FORMAT_TEXT_RECORD, formatted_print

from ._common import endpoint_create_params, validate_endpoint_create_and_update_params

COMMON_FIELDS = [("Message", "message"), ("Endpoint ID", "id")]

GCP_FIELDS = [("Setup Key", "globus_connect_setup_key")]


@command(
    "create",
    short_help="Create a new endpoint",
    adoc_examples="""Create a Globus Connect Personal endpoint:

[source,bash]
----
$ globus endpoint create --personal my_gcp_endpoint
----

Create a Globus Connect Server endpoint:

[source,bash]
----
$ globus endpoint create --server my_gcs_endpoint
----

Create a shared endpoint hosted on another endpoint:

[source,bash]
----
$ host_ep=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus endpoint create --shared host_ep:~/ my_shared_endpoint
----
""",
)
@endpointish_create_and_update_params("create")
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
    Create a new endpoint. (deprecated)

    This command is deprecated. Either `globus gcp create` or the Globus Connect Server
    CLI should be used instead for most cases.

    Requires a display name and exactly one of --personal, --server, or --shared to make
    a Globus Connect Personal, Globus Connect Server, or Shared endpoint respectively.

    Note that `--personal` does not perform local setup steps. When this command is run
    with the `--personal` flag, it returns a setup key which can be passed to
    Globus Connect Personal during setup.
    """
    from globus_cli.services.transfer import assemble_generic_doc, autoactivate

    transfer_client = login_manager.get_transfer_client()

    endpoint_type = "personal" if personal else "server" if server else "shared"

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
    formatted_print(
        res,
        fields=(COMMON_FIELDS + GCP_FIELDS if personal else COMMON_FIELDS),
        text_format=FORMAT_TEXT_RECORD,
    )
