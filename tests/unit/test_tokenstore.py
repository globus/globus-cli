import uuid

import globus_sdk
from globus_sdk.testing import RegisteredResponse, get_last_request

from globus_cli.login_manager.storage import CLIStorage, _resolve_namespace


def test_default_namespace():
    assert _resolve_namespace() == "userprofile/production"


def test_profile_namespace(user_profile):
    assert _resolve_namespace() == "userprofile/production/test_user_profile"


def test_client_namespace(client_login):
    assert _resolve_namespace() == "clientprofile/production/fake_client_id"


def test_storage_reuses_clients():
    # confirm that we do not recreate clients when we need to use them multiple times
    #
    # these are instrumented via `@functools.cached_property`
    # if we switch to `@property` we must choose an implementation which
    # does not regress this test
    storage = CLIStorage()

    confidential1 = storage.cli_confidential_client
    confidential2 = storage.cli_confidential_client
    assert confidential1 is confidential2

    native1 = storage.cli_native_client
    native2 = storage.cli_native_client
    assert native1 is native2


def test_storage_creates_fresh_client_after_delete():
    RegisteredResponse(
        service="auth",
        path="/v2/api/clients/fakeClientIDString",
        method="DELETE",
        status=200,
        json={},
    ).add()
    RegisteredResponse(
        service="auth",
        path="/v2/api/clients",
        method="POST",
        status=200,
        json={
            "included": {
                "client_credential": {
                    "client": str(uuid.UUID(int=1)),
                    "secret": "bogusBOGUSbogus",
                }
            }
        },
    ).add()
    # note: the `patch_tokenstorage` fixture in top-level conftest.py ensures
    # that we get a memory backed DB with pre-existing client credentials
    storage = CLIStorage()

    # before delete: we have a client and data for that client
    client1 = storage.cli_confidential_client
    assert isinstance(client1, globus_sdk.ConfidentialAppAuthClient)
    client_data1 = storage.read_well_known_config("auth_client_data")
    assert client_data1 is not None

    storage.delete_templated_client()

    # after delete: no client data, fetching a client creates a new one
    client_data2 = storage.read_well_known_config("auth_client_data")
    assert client_data2 is None

    client2 = storage.cli_confidential_client
    assert client1 is not client2

    last_req = get_last_request()
    assert last_req.method == "POST"
    assert last_req.url.endswith("/v2/api/clients")
