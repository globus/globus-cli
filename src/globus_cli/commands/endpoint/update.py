from globus_cli.endpointish import Endpointish
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg, endpointish_setattr_params
from globus_cli.termio import TextMode, display

from ._common import endpoint_update_params, validate_endpoint_create_and_update_params


@command("update")
@endpoint_id_arg
@endpoint_update_params
@endpointish_setattr_params("update")
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def endpoint_update(*, login_manager: LoginManager, **kwargs):
    """Update attributes of an endpoint"""
    from globus_cli.services.transfer import assemble_generic_doc

    transfer_client = login_manager.get_transfer_client()
    endpoint_id = kwargs.pop("endpoint_id")

    epish = Endpointish(endpoint_id, transfer_client=transfer_client)
    epish.assert_is_traditional_endpoint()

    if epish.data["host_endpoint_id"]:
        endpoint_type = "shared"
    elif epish.data["is_globus_connect"]:
        endpoint_type = "personal"
    elif epish.data["s3_url"]:
        endpoint_type = "s3"
    else:
        endpoint_type = "server"
    validate_endpoint_create_and_update_params(
        endpoint_type, epish.data["subscription_id"], kwargs
    )

    # make the update
    ep_doc = assemble_generic_doc("endpoint", **kwargs)
    res = transfer_client.update_endpoint(endpoint_id, ep_doc)
    display(res, text_mode=TextMode.text_raw, response_key="message")
