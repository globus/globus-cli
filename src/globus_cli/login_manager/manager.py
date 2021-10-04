import functools
from typing import Dict, Generator, List, Optional, Tuple

import click
import globus_sdk
from globus_sdk.scopes import AuthScopes, GroupsScopes, SearchScopes, TransferScopes

from .auth_flows import do_link_auth_flow, do_local_server_auth_flow
from .errors import MissingLoginError
from .local_server import is_remote_session
from .tokenstore import internal_auth_client, token_storage_adapter


class LoginManager:
    # TEST_MODE skips token validation
    _TEST_MODE: bool = False

    AUTH_RS = AuthScopes.resource_server
    TRANSFER_RS = TransferScopes.resource_server
    GROUPS_RS = GroupsScopes.resource_server
    SEARCH_RS = SearchScopes.resource_server

    STATIC_SCOPES: Dict[str, List[str]] = {
        AUTH_RS: [
            AuthScopes.openid,
            AuthScopes.profile,
            AuthScopes.email,
            AuthScopes.view_identity_set,
        ],
        TRANSFER_RS: [
            TransferScopes.all,
        ],
        GROUPS_RS: [
            GroupsScopes.all,
        ],
        SEARCH_RS: [
            SearchScopes.all,
        ],
    }

    def __init__(self) -> None:
        self._token_storage = token_storage_adapter()
        self._nonstatic_requirements: Dict[str, List[str]] = {}

    def add_requirement(self, rs_name: str, scopes: List[str]) -> None:
        self._nonstatic_requirements[rs_name] = scopes

    @property
    def login_requirements(self) -> Generator[Tuple[str, List[str]], None, None]:
        yield from self.STATIC_SCOPES.items()
        yield from self._nonstatic_requirements.items()

    def is_logged_in(self) -> bool:
        res = []
        for rs_name, _scopes in self.login_requirements:
            res.append(self.has_login(rs_name))
        return all(res)

    def _validate_token(self, token: str) -> bool:
        if self._TEST_MODE:
            return True

        auth_client = internal_auth_client()
        try:
            res = auth_client.oauth2_validate_token(token)
        # if the instance client is invalid, an AuthAPIError will be raised
        except globus_sdk.AuthAPIError:
            return False
        return bool(res["active"])

    def has_login(self, resource_server: str) -> bool:
        """
        Determines if the user has a valid refresh token for the given
        resource server
        """
        tokens = self._token_storage.get_token_data(resource_server)
        if tokens is None or "refresh_token" not in tokens:
            return False
        rt = tokens["refresh_token"]
        return self._validate_token(rt)

    def run_login_flow(
        self,
        *,
        no_local_server: bool = False,
        local_server_message: Optional[str] = None,
        epilog: Optional[str] = None,
        session_params: Optional[dict] = None,
        scopes: Optional[List[str]] = None,
    ):
        if scopes is None:  # flatten scopes to list of strings if none provided
            scopes = [
                s for _rs_name, rs_scopes in self.login_requirements for s in rs_scopes
            ]
        # use a link login if remote session or user requested
        if no_local_server or is_remote_session():
            do_link_auth_flow(scopes, session_params=session_params)
        # otherwise default to a local server login flow
        else:
            if local_server_message is not None:
                click.echo(local_server_message)
            do_local_server_auth_flow(scopes, session_params=session_params)

        if epilog is not None:
            click.echo(epilog)

    def assert_logins(self, *resource_servers, assume_gcs=False):
        # determine the set of resource servers missing logins
        missing_servers = {s for s in resource_servers if not self.has_login(s)}

        # if we are missing logins, assemble error text
        # text is slightly different for 1, 2, or 3+ missing servers
        if missing_servers:
            raise MissingLoginError(missing_servers, assume_gcs=assume_gcs)

    @classmethod
    def requires_login(cls, *resource_servers: str, pass_manager: bool = False):
        """
        Command decorator for specifying a resource server that the user must have
        tokens for in order to run the command.

        Simple usage for commands that have static resource needs: simply list all
        needed resource servers as args:

        @LoginManager.requries_login("auth.globus.org")

        @LoginManager.requries_login(LoginManager.AUTH_RS)

        @LoginManager.requires_login("auth.globus.org", "transfer.api.globus.org")

        @LoginManager.requries_login(LoginManager.AUTH_RS, LoginManager.TRANSFER_RS)

        Usage for commands which have dynamic resource servers depending
        on the arguments passed to the command (e.g. commands for the GCS API)

        @LoginManager.requies_login(pass_manager=True)
        def command(login_manager, endpoint_id)

            login_manager.<do the thing>(endpoint_id)

        """

        def inner(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                manager = cls()
                manager.assert_logins(*resource_servers)
                # if pass_manager is True, pass it as an additional positional arg
                if pass_manager:
                    return func(*args, manager, **kwargs)
                else:
                    return func(*args, **kwargs)

            return wrapper

        return inner
