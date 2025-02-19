import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import collection_id_arg, command
from globus_cli.termio import display


@command("delete", short_help="Delete an existing Collection.")
@collection_id_arg
@LoginManager.requires_login("transfer")
def collection_delete(login_manager: LoginManager, *, collection_id: uuid.UUID) -> None:
    """
    Delete an existing Collection.

    This requires that you are an owner or administrator on the Collection.

    Endpoint owners and administrators may delete Collections on the Endpoint.
    For Guest Collections, administrators of the Mapped Collection may also delete.

    If the collection has the 'delete_protection' property set to true, the Collection
    can not be deleted.

    All Collection-specific roles and 'sharing_policies' are also deleted.

    If a Mapped Collection is deleted, then all Guest Collections and roles associated
    with it are also deleted.
    """
    gcs_client = login_manager.get_gcs_client(collection_id=collection_id)
    res = gcs_client.delete_collection(collection_id)
    display(res, text_mode=display.RAW, response_key="code")
