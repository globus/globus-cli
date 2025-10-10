from __future__ import annotations

import functools
import os
import sys
import typing as t

import globus_sdk
from globus_sdk.token_storage.legacy import SQLiteAdapter

from ._old_config import invalidate_old_config
from .client_login import get_client_login, is_client_login
from .scopes import CURRENT_SCOPE_CONTRACT_VERSION

# env vars used throughout this module
GLOBUS_ENV = os.environ.get("GLOBUS_SDK_ENVIRONMENT")


class CLIStorage:
    """
    A wrapper over the globus-sdk's v1 tokenstorage which provides simplified
    capabilities specific to the CLI.
    """

    def __init__(self) -> None:
        self.adapter: SQLiteAdapter = self._construct_adapter()

    def _construct_adapter(self) -> SQLiteAdapter:
        # when initializing the token storage adapter, check if the storage file exists
        # if it does not, then use this as a flag to clean the old config
        fname = _get_storage_filename()
        if not os.path.exists(fname):
            invalidate_old_config(self.cli_native_client)

        return SQLiteAdapter(fname, namespace=_resolve_namespace())

    def close(self) -> None:
        self.adapter.close()

    @functools.cached_property
    def cli_native_client(self) -> globus_sdk.NativeAppAuthClient:
        """
        This is the client that represents the CLI itself (prior to templating).
        """
        template_id = _template_client_id()
        return globus_sdk.NativeAppAuthClient(
            template_id, app_name="Globus CLI (native client)"
        )

    @functools.cached_property
    def cli_confidential_client(self) -> globus_sdk.ConfidentialAppAuthClient:
        """
        Get the client which represents the CLI as a templated app, as distinct from a
        confidential client built from a user's credentials.

        In the event that credentials are not found, template a new client via the
        Auth API, save the credentials for that client, and then build and return the
        ConfidentialAppAuthClient.
        """
        if is_client_login():
            raise ValueError("client logins shouldn't create internal auth clients")

        client_data = self.read_well_known_config("auth_client_data")
        if client_data is not None:
            client_id = client_data["client_id"]
            client_secret = client_data["client_secret"]
        else:
            # register a new instance client with auth
            nc = self.cli_native_client
            res = nc.post(
                "/v2/api/clients",
                data={"client": {"template_id": nc.client_id, "name": "Globus CLI"}},
            )
            # get values and write to config
            credential_data = res["included"]["client_credential"]
            client_id = credential_data["client"]
            client_secret = credential_data["secret"]

            self.store_well_known_config(
                "auth_client_data",
                {"client_id": client_id, "client_secret": client_secret},
            )

        return globus_sdk.ConfidentialAppAuthClient(
            client_id, client_secret, app_name="Globus CLI"
        )

    def delete_templated_client(self) -> None:
        # first, get the templated credentialed client
        ac = self.cli_confidential_client

        # now, remove its relevant data from storage
        self.remove_well_known_config("auth_client_data")
        self.remove_well_known_config("scope_contract_versions")

        # finally, try to delete via the API
        # note that this could raise an exception if the creds are already invalid --
        # the caller may or may not want to ignore, so allow it to raise from here
        ac.delete(f"/v2/api/clients/{ac.client_id}")

        # clear the cached_property
        del self.cli_confidential_client

    def store_well_known_config(
        self,
        name: t.Literal[
            "auth_client_data", "auth_user_data", "scope_contract_versions"
        ],
        data: dict[str, t.Any],
    ) -> None:
        self.adapter.store_config(name, data)

    @t.overload
    def read_well_known_config(
        self,
        name: t.Literal[
            "auth_client_data", "auth_user_data", "scope_contract_versions"
        ],
        *,
        allow_null: t.Literal[False],
    ) -> dict[str, t.Any]: ...

    @t.overload
    def read_well_known_config(
        self,
        name: t.Literal[
            "auth_client_data", "auth_user_data", "scope_contract_versions"
        ],
        *,
        allow_null: bool = True,
    ) -> dict[str, t.Any] | None: ...

    def read_well_known_config(
        self,
        name: t.Literal[
            "auth_client_data", "auth_user_data", "scope_contract_versions"
        ],
        *,
        allow_null: bool = True,
    ) -> dict[str, t.Any] | None:
        data = self.adapter.read_config(name)
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
        self,
        name: t.Literal[
            "auth_client_data", "auth_user_data", "scope_contract_versions"
        ],
    ) -> None:
        self.adapter.remove_config(name)

    def store(self, token_response: globus_sdk.OAuthTokenResponse) -> None:
        self.adapter.store(token_response)
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
        contract_versions: dict[str, t.Any] | None = self.read_well_known_config(
            "scope_contract_versions"
        )
        if contract_versions is None:
            contract_versions = {}
        for rs_name in token_response.by_resource_server:
            contract_versions[rs_name] = CURRENT_SCOPE_CONTRACT_VERSION
        self.store_well_known_config("scope_contract_versions", contract_versions)


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
