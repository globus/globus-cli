from __future__ import annotations

import functools
import typing as t
import uuid

import click
import globus_sdk
from globus_sdk.scopes import (
    AuthScopes,
    FlowsScopes,
    GCSEndpointScopeBuilder,
    GroupsScopes,
    SearchScopes,
    TimerScopes,
    TransferScopes,
)

from globus_cli.endpointish import Endpointish, EndpointType

from .. import version
from .auth_flows import do_link_auth_flow, do_local_server_auth_flow
from .client_login import get_client_login, is_client_login
from .errors import MissingLoginError
from .tokenstore import internal_auth_client, token_storage_adapter
from .utils import is_remote_session

if t.TYPE_CHECKING:
    from ..services.auth import CustomAuthClient
    from ..services.gcs import CustomGCSClient
    from ..services.transfer import CustomTransferClient


class LoginManager:
    # TEST_MODE skips token validation
    _TEST_MODE: bool = False

    AUTH_RS = AuthScopes.resource_server
    FLOWS_RS = FlowsScopes.resource_server
    GROUPS_RS = GroupsScopes.resource_server
    SEARCH_RS = SearchScopes.resource_server
    TIMER_RS = TimerScopes.resource_server
    TRANSFER_RS = TransferScopes.resource_server

    STATIC_SCOPES: dict[str, list[str]] = {
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
        TIMER_RS: [
            TimerScopes.timer,
        ],
        FLOWS_RS: [
            FlowsScopes.manage_flows,
            FlowsScopes.view_flows,
            FlowsScopes.run,
            FlowsScopes.run_status,
            FlowsScopes.run_manage,
        ],
    }

    def __init__(self) -> None:
        self._token_storage = token_storage_adapter()
        self._nonstatic_requirements: dict[str, list[str]] = {}

    def add_requirement(self, rs_name: str, scopes: list[str]) -> None:
        self._nonstatic_requirements[rs_name] = scopes

    @property
    def login_requirements(self) -> t.Iterator[tuple[str, list[str]]]:
        yield from self.STATIC_SCOPES.items()
        yield from self._nonstatic_requirements.items()

    @property
    def always_required_scopes(self) -> t.Iterator[str]:
        """
        scopes which are required on all login flows, regardless of the specified
        scopes for that flow
        """
        # openid -> required to ensure the presence of an id_token in the response data
        # WARNING:
        # all other Auth scopes are required the moment we add 'openid'
        # adding 'openid' without other scopes gives us back an Auth token which is not
        # valid for the other necessary scopes
        yield from self.STATIC_SCOPES[self.AUTH_RS]

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
        # client identities are always logged in
        if is_client_login():
            return True

        tokens = self._token_storage.get_token_data(resource_server)
        if tokens is None or "refresh_token" not in tokens:
            return False
        rt = tokens["refresh_token"]
        return self._validate_token(rt)

    def run_login_flow(
        self,
        *,
        no_local_server: bool = False,
        local_server_message: str | None = None,
        epilog: str | None = None,
        session_params: dict | None = None,
        scopes: list[str] | None = None,
    ):
        if is_client_login():
            click.echo(
                "Client identities do not need to log in. If you are trying "
                "to do a user log in, please unset the GLOBUS_CLI_CLIENT_ID "
                "and GLOBUS_CLI_CLIENT_SECRET environment variables."
            )
            click.get_current_context().exit(1)

        if scopes is None:  # flatten scopes to list of strings if none provided
            scopes = [
                s for _rs_name, rs_scopes in self.login_requirements for s in rs_scopes
            ]
        # ensure that the requested scope list contains the scopes which are listed as
        # "always required"
        for s in self.always_required_scopes:
            if s not in scopes:
                scopes.append(s)
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
    def requires_login(cls, *resource_servers: str):
        """
        Command decorator for specifying a resource server that the user must have
        tokens for in order to run the command.

        Simple usage for commands that have static resource needs: simply list all
        needed resource servers as args:

        @LoginManager.requires_login("auth.globus.org")

        @LoginManager.requires_login(LoginManager.AUTH_RS)

        @LoginManager.requires_login("auth.globus.org", "transfer.api.globus.org")

        @LoginManager.requires_login(LoginManager.AUTH_RS, LoginManager.TRANSFER_RS)

        Usage for commands which have dynamic resource servers depending
        on the arguments passed to the command (e.g. commands for the GCS API)

        @LoginManager.requires_login()
        def command(login_manager, endpoint_id)

            login_manager.<do the thing>(endpoint_id)

        """

        def inner(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                manager = cls()
                manager.assert_logins(*resource_servers)
                return func(*args, login_manager=manager, **kwargs)

            return wrapper

        return inner

    def _get_client_authorizer(
        self, resource_server: str, *, no_tokens_msg: str | None = None
    ) -> globus_sdk.authorizers.RenewingAuthorizer:
        tokens = self._token_storage.get_token_data(resource_server)

        if is_client_login():
            # construct scopes for the specified resource server.
            # this is not guaranteed to contain always required scopes,
            # additional logic may be needed to handle client identities that
            # may be missing those.
            scopes = []
            for rs_name, rs_scopes in self.login_requirements:
                if rs_name == resource_server:
                    scopes.extend(rs_scopes)

            # if we already have a token use it. This token could be invalid
            # or for another client, but automatic retries will handle that
            access_token = None
            expires_at = None
            if tokens:
                access_token = tokens["access_token"]
                expires_at = tokens["expires_at_seconds"]

            return globus_sdk.ClientCredentialsAuthorizer(
                confidential_client=get_client_login(),
                scopes=scopes,
                access_token=access_token,
                expires_at=expires_at,
                on_refresh=self._token_storage.on_refresh,
            )

        else:
            # tokens are required for user logins
            if tokens is None:
                raise ValueError(
                    no_tokens_msg
                    or (
                        f"Could not get login data for {resource_server}."
                        " Try login to fix."
                    )
                )

            return globus_sdk.RefreshTokenAuthorizer(
                tokens["refresh_token"],
                internal_auth_client(),
                access_token=tokens["access_token"],
                expires_at=tokens["expires_at_seconds"],
                on_refresh=self._token_storage.on_refresh,
            )

    def get_transfer_client(self) -> CustomTransferClient:
        from ..services.transfer import CustomTransferClient

        authorizer = self._get_client_authorizer(TransferScopes.resource_server)
        return CustomTransferClient(authorizer=authorizer, app_name=version.app_name)

    def get_auth_client(self) -> CustomAuthClient:
        from ..services.auth import CustomAuthClient

        authorizer = self._get_client_authorizer(AuthScopes.resource_server)
        return CustomAuthClient(authorizer=authorizer, app_name=version.app_name)

    def get_groups_client(self) -> globus_sdk.GroupsClient:
        authorizer = self._get_client_authorizer(GroupsScopes.resource_server)
        return globus_sdk.GroupsClient(authorizer=authorizer, app_name=version.app_name)

    def get_flows_client(self) -> globus_sdk.FlowsClient:
        authorizer = self._get_client_authorizer(FlowsScopes.resource_server)
        return globus_sdk.FlowsClient(authorizer=authorizer, app_name=version.app_name)

    def get_search_client(self) -> globus_sdk.SearchClient:
        authorizer = self._get_client_authorizer(SearchScopes.resource_server)
        return globus_sdk.SearchClient(authorizer=authorizer, app_name=version.app_name)

    def get_timer_client(self) -> globus_sdk.TimerClient:
        authorizer = self._get_client_authorizer(TimerScopes.resource_server)
        return globus_sdk.TimerClient(authorizer=authorizer, app_name=version.app_name)

    def _get_gcs_info(
        self,
        *,
        collection_id: uuid.UUID | None = None,
        endpoint_id: uuid.UUID | None = None,
    ) -> tuple[str, Endpointish]:
        if collection_id is not None and endpoint_id is not None:  # pragma: no cover
            raise ValueError("Internal Error! collection_id and endpoint_id are mutex")

        transfer_client = self.get_transfer_client()

        if collection_id is not None:
            epish = Endpointish(collection_id, transfer_client=transfer_client)
            resolved_ep_id = epish.get_collection_endpoint_id()
        elif endpoint_id is not None:
            epish = Endpointish(endpoint_id, transfer_client=transfer_client)
            epish.assert_ep_type(EndpointType.GCSV5_ENDPOINT)
            resolved_ep_id = str(endpoint_id)
        else:  # pragma: no cover
            raise ValueError("Internal Error! collection_id or endpoint_id is required")
        return (resolved_ep_id, epish)

    def get_gcs_client(
        self,
        *,
        collection_id: uuid.UUID | None = None,
        endpoint_id: uuid.UUID | None = None,
    ) -> CustomGCSClient:
        from ..services.gcs import CustomGCSClient

        gcs_id, epish = self._get_gcs_info(
            collection_id=collection_id, endpoint_id=endpoint_id
        )

        # client identities need to have this scope added as a requirement
        # so that they correctly request it when building authorizers
        self.add_requirement(
            gcs_id, scopes=[GCSEndpointScopeBuilder(gcs_id).manage_collections]
        )
        self.assert_logins(gcs_id, assume_gcs=True)

        authorizer = self._get_client_authorizer(
            gcs_id,
            no_tokens_msg=(
                f"Could not get login data for GCS {gcs_id}. "
                f"Try login with '--gcs {gcs_id}' to fix."
            ),
        )
        return CustomGCSClient(
            epish.get_gcs_address(),
            source_epish=epish,
            authorizer=authorizer,
            app_name=version.app_name,
        )
