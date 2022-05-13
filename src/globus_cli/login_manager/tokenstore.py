import os
import sys
from typing import cast

import globus_sdk
from globus_sdk.tokenstorage import SQLiteAdapter

from .client_login import get_client_login, is_client_login

# internal constants
_CLIENT_DATA_CONFIG_KEY = "auth_client_data"

# env vars used throughout this module
GLOBUS_ENV = os.environ.get("GLOBUS_SDK_ENVIRONMENT")


# stub to allow type casting of a function to an object with an attribute
class _TokenStoreFuncProto:
    _instance: SQLiteAdapter


def _template_client_id():
    template_id = "95fdeba8-fac2-42bd-a357-e068d82ff78e"
    if GLOBUS_ENV:
        template_id = {
            "sandbox": "33b6a241-bce4-4359-9c6d-09f88b3c9eef",
            "integration": "e0c31fd1-663b-44e1-840f-f4304bb9ee7a",
            "test": "0ebfd058-452f-40c3-babf-5a6b16a7b337",
            "staging": "3029c3cb-c8d9-4f2b-979c-c53330aa7327",
            "preview": "b2867dbb-0846-4579-8486-dc70763d700b",
        }.get(GLOBUS_ENV, template_id)
    return template_id


def internal_native_client():
    """
    This is the client that represents the CLI itself (prior to templating)
    """
    template_id = _template_client_id()
    return globus_sdk.NativeAppAuthClient(
        template_id, app_name="Globus CLI (native client)"
    )


def _get_data_dir():
    # get the dir to store Globus CLI data
    #
    # on Windows, the datadir is typically
    #   ~\AppData\Local\globus\cli
    #
    # on Linux and macOS, we use
    #   ~/.globus/cli/
    #
    # This is not necessarily a match with XDG_DATA_HOME or macOS use of
    # '~/Library/Application Support'. The simplified directories for non-Windows
    # platforms will allow easier access to the dir if necessary in support of users
    if sys.platform == "win32":
        # try to get the app data dir, preferring the local appdata
        datadir = os.getenv("LOCALAPPDATA", os.getenv("APPDATA"))
        if not datadir:
            home = os.path.expanduser("~")
            datadir = os.path.join(home, "AppData", "Local")
        return os.path.join(datadir, "globus", "cli")
    else:
        return os.path.expanduser("~/.globus/cli/")


def _ensure_data_dir():
    dirname = _get_data_dir()
    try:
        os.makedirs(dirname)
    except FileExistsError:
        pass
    return dirname


def _get_storage_filename():
    datadir = _ensure_data_dir()
    return os.path.join(datadir, "storage.db")


def _resolve_namespace():
    """
    expected user namespaces are:

    userprofile/production        (default)
    userprofile/sandbox           (env is set to sandbox)
    userprofile/test/myprofile    (env is set to test, profile is set to myprofile)

    client namespaces ignore profile, and include client_id in the namespace:

    clientprofile/production/926cc9c6-b481-4a5e-9ccd-b497f04c643b (default)
    clientprofile/sandbox/926cc9c6-b481-4a5e-9ccd-b497f04c643b    (sandbox env)
    """
    env = GLOBUS_ENV if GLOBUS_ENV else "production"
    profile = os.environ.get("GLOBUS_PROFILE")

    if is_client_login():
        client_id = get_client_login().client_id
        return f"clientprofile/{env}/{client_id}"

    else:
        return "userprofile/" + env + (f"/{profile}" if profile else "")


def token_storage_adapter() -> SQLiteAdapter:
    as_proto = cast(_TokenStoreFuncProto, token_storage_adapter)
    if not hasattr(as_proto, "_instance"):
        # when initializing the token storage adapter, check if the storage file exists
        # if it does not, then use this as a flag to clean the old config
        fname = _get_storage_filename()
        if not os.path.exists(fname):
            from ._old_config import invalidate_old_config

            invalidate_old_config(internal_native_client())
        # namespace is equal to the current environment
        as_proto._instance = SQLiteAdapter(fname, namespace=_resolve_namespace())
    return as_proto._instance


def internal_auth_client():
    """
    Pull template client credentials from storage and use them to create a
    ConfidentialAppAuthClient.
    In the event that credentials are not found, template a new client via the Auth API,
    save the credentials for that client, and then build and return the
    ConfidentialAppAuthClient.
    """
    if is_client_login():
        raise ValueError("client logins shouldn't create internal auth clients")

    adapter = token_storage_adapter()
    client_data = adapter.read_config(_CLIENT_DATA_CONFIG_KEY)
    if client_data is not None:
        client_id = client_data["client_id"]
        client_secret = client_data["client_secret"]
    else:
        # register a new instance client with auth
        nc = internal_native_client()
        res = nc.post(
            "/v2/api/clients",
            data={"client": {"template_id": nc.client_id, "name": "Globus CLI"}},
        )
        # get values and write to config
        credential_data = res["included"]["client_credential"]
        client_id = credential_data["client"]
        client_secret = credential_data["secret"]

        adapter.store_config(
            _CLIENT_DATA_CONFIG_KEY,
            {"client_id": client_id, "client_secret": client_secret},
        )

    return globus_sdk.ConfidentialAppAuthClient(
        client_id, client_secret, app_name="Globus CLI"
    )


def delete_templated_client():
    adapter = token_storage_adapter()

    # first, get the templated credentialed client
    ac = internal_auth_client()

    # now, remove its relevant data from storage
    adapter.remove_config(_CLIENT_DATA_CONFIG_KEY)

    # finally, try to delete via the API
    # note that this could raise an exception if the creds are already invalid -- the
    # caller may or may not want to ignore, so allow it to raise from here
    ac.delete(f"/v2/api/clients/{ac.client_id}")
