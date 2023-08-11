from __future__ import annotations

import os
import sys
import typing as t

import globus_sdk

from .client_login import get_client_login, is_client_login
from .scopes import CURRENT_SCOPE_CONTRACT_VERSION

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

if t.TYPE_CHECKING:
    from globus_sdk.tokenstorage import SQLiteAdapter

# env vars used throughout this module
GLOBUS_ENV = os.environ.get("GLOBUS_SDK_ENVIRONMENT")


# stub to allow type casting of a function to an object with an attribute
class _TokenStoreFuncProto:
    _instance: SQLiteAdapter


def _template_client_id() -> str:
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


def internal_native_client() -> globus_sdk.NativeAppAuthClient:
    """
    This is the client that represents the CLI itself (prior to templating)
    """
    template_id = _template_client_id()
    return globus_sdk.NativeAppAuthClient(
        template_id, app_name="Globus CLI (native client)"
    )


def _get_data_dir() -> str:
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


def _ensure_data_dir() -> str:
    dirname = _get_data_dir()
    try:
        os.makedirs(dirname)
    except FileExistsError:
        pass
    return dirname


def _get_storage_filename() -> str:
    datadir = _ensure_data_dir()
    return os.path.join(datadir, "storage.db")


def _resolve_namespace() -> str:
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


def build_storage_adapter(fname: str) -> SQLiteAdapter:
    """
    Customize the SQLiteAdapter with extra storage operation steps
    In order to avoid eager imports, which have a perf impact on the CLI, we need to
    define the class dynamically in this function.
    """
    from globus_sdk.tokenstorage import SQLiteAdapter

    class GeneratedAdapterClass(SQLiteAdapter):
        def store(self, token_response: globus_sdk.OAuthTokenResponse) -> None:
            super().store(token_response)
            # store contract versions for all of the tokens which were acquired
            # this could overwrite data from another CLI version *earlier or later* than
            # the current one
            #
            # in the case that the old data was from a prior version, this makes sense
            # because we have added new constraints or behaviors
            #
            # if the data was from a *newer* CLI version than what we are currently
            # running we can't really know with certainty that "downgrading" the version
            # numbers is correct, but because we can't know we need to just do our best
            # to indicate that the tokens in storage may have lost capabilities
            contract_versions: dict[str, t.Any] | None = read_well_known_config(
                "scope_contract_versions", adapter=self
            )
            if contract_versions is None:
                contract_versions = {}
            for rs_name in token_response.by_resource_server:
                contract_versions[rs_name] = CURRENT_SCOPE_CONTRACT_VERSION
            store_well_known_config(
                "scope_contract_versions", contract_versions, adapter=self
            )

    return GeneratedAdapterClass(fname, namespace=_resolve_namespace())


def token_storage_adapter() -> SQLiteAdapter:
    as_proto = t.cast(_TokenStoreFuncProto, token_storage_adapter)
    if not hasattr(as_proto, "_instance"):
        # when initializing the token storage adapter, check if the storage file exists
        # if it does not, then use this as a flag to clean the old config
        fname = _get_storage_filename()
        if not os.path.exists(fname):
            from ._old_config import invalidate_old_config

            invalidate_old_config(internal_native_client())
        # namespace is equal to the current environment
        as_proto._instance = build_storage_adapter(fname)
    return as_proto._instance


def internal_auth_client() -> globus_sdk.ConfidentialAppAuthClient:
    """
    Pull template client credentials from storage and use them to create a
    ConfidentialAppAuthClient.
    In the event that credentials are not found, template a new client via the Auth API,
    save the credentials for that client, and then build and return the
    ConfidentialAppAuthClient.
    """
    if is_client_login():
        raise ValueError("client logins shouldn't create internal auth clients")

    client_data = read_well_known_config("auth_client_data")
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

        store_well_known_config(
            "auth_client_data",
            {"client_id": client_id, "client_secret": client_secret},
        )

    return globus_sdk.ConfidentialAppAuthClient(
        client_id, client_secret, app_name="Globus CLI"
    )


def delete_templated_client() -> None:
    # first, get the templated credentialed client
    ac = internal_auth_client()

    # now, remove its relevant data from storage
    remove_well_known_config("auth_client_data")
    remove_well_known_config("scope_contract_versions")

    # finally, try to delete via the API
    # note that this could raise an exception if the creds are already invalid -- the
    # caller may or may not want to ignore, so allow it to raise from here
    ac.delete(f"/v2/api/clients/{ac.client_id}")


def store_well_known_config(
    name: Literal["auth_client_data", "auth_user_data", "scope_contract_versions"],
    data: dict[str, t.Any],
    *,
    adapter: SQLiteAdapter | None = None,
) -> None:
    adapter = adapter or token_storage_adapter()
    adapter.store_config(name, data)


@t.overload
def read_well_known_config(
    name: Literal["auth_client_data", "auth_user_data", "scope_contract_versions"],
    *,
    adapter: SQLiteAdapter | None = None,
    allow_null: Literal[False],
) -> dict[str, t.Any]:
    ...


@t.overload
def read_well_known_config(
    name: Literal["auth_client_data", "auth_user_data", "scope_contract_versions"],
    *,
    adapter: SQLiteAdapter | None = None,
    allow_null: bool = True,
) -> dict[str, t.Any] | None:
    ...


def read_well_known_config(
    name: Literal["auth_client_data", "auth_user_data", "scope_contract_versions"],
    *,
    adapter: SQLiteAdapter | None = None,
    allow_null: bool = True,
) -> dict[str, t.Any] | None:
    adapter = adapter or token_storage_adapter()
    data = adapter.read_config(name)
    if not allow_null and data is None:
        if name == "auth_user_data":
            alias = "Identity Info"
        else:
            alias = name
        raise RuntimeError(
            f"{alias} was unexpectedly not visible in storage. "
            "A new login should fix the issue. "
            "Consider using `globus login --force`"
        )
    return data


def remove_well_known_config(
    name: Literal["auth_client_data", "auth_user_data", "scope_contract_versions"],
    *,
    adapter: SQLiteAdapter | None = None,
) -> None:
    adapter = adapter or token_storage_adapter()
    adapter.remove_config(name)
