from __future__ import annotations

import functools
import sys
import typing as t
import uuid

import click
import globus_sdk
from globus_sdk.experimental.consents import ConsentForest
from globus_sdk.experimental.scope_parser import Scope
from globus_sdk.scopes import (
    AuthScopes,
    FlowsScopes,
    GCSCollectionScopeBuilder,
    GCSEndpointScopeBuilder,
    GroupsScopes,
    MutableScope,
    SearchScopes,
    TransferScopes,
)

from globus_cli.endpointish import Endpointish, EntityType
from globus_cli.types import ServiceNameLiteral

from .. import version
from .auth_flows import do_link_auth_flow, do_local_server_auth_flow
from .client_login import get_client_login, is_client_login
from .context import LoginContext
from .errors import MissingLoginError
from .scopes import CLI_SCOPE_REQUIREMENTS
from .tokenstore import (
    internal_auth_client,
    read_well_known_config,
    token_storage_adapter,
)
from .utils import get_current_identity_id, is_remote_session

# TODO: remove this after an SDK release provides TimersScopes
try:
    from globus_sdk.scopes import TimersScopes
except ImportError:
    from globus_sdk.scopes import TimerScopes as TimersScopes

if t.TYPE_CHECKING:
    from ..services.auth import CustomAuthClient
    from ..services.gcs import CustomGCSClient
    from ..services.transfer import CustomTransferClient

if sys.version_info >= (3, 10):
    from typing import Concatenate, ParamSpec
else:
    from typing_extensions import Concatenate, ParamSpec

P = ParamSpec("P")
R = t.TypeVar("R")


class LoginManager:
    def __init__(self) -> None:
        self._token_storage = token_storage_adapter()
        self._nonstatic_requirements: dict[str, list[str | MutableScope]] = {}

    def add_requirement(
        self, rs_name: str, scopes: t.Sequence[str | MutableScope]
    ) -> None:
        self._nonstatic_requirements[rs_name] = list(scopes)

    @property
    def login_requirements(self) -> t.Iterator[tuple[str, list[str | MutableScope]]]:
        for req in CLI_SCOPE_REQUIREMENTS.values():
            yield req["resource_server"], req["scopes"]
        yield from self._nonstatic_requirements.items()

    @property
    def always_required_scopes(self) -> t.Iterator[str | MutableScope]:
        """
        scopes which are required on all login flows, regardless of the specified
        scopes for that flow
        """
        # openid -> required to ensure the presence of an id_token in the response data
        # WARNING:
        # all other Auth scopes are required the moment we add 'openid'
        # adding 'openid' without other scopes gives us back an Auth token which is not
        # valid for the other necessary scopes
        yield from CLI_SCOPE_REQUIREMENTS["auth"]["scopes"]

    def is_logged_in(self) -> bool:
        return all(
            self.has_login(rs_name) for rs_name, _scopes in self.login_requirements
        )

    def _validate_token(self, token: str) -> bool:
        auth_client = internal_auth_client()
        try:
            res = auth_client.post(
                "/v2/oauth2/token/validate", data={"token": token}, encoding="form"
            )
        # if the instance client is invalid, an AuthAPIError will be raised
        except globus_sdk.AuthAPIError:
            return False
        return bool(res["active"])

    def has_login(self, resource_server: str) -> bool:
        """
        Determines whether the user
          1. has an active refresh token for the given server in the local tokenstore
             which meets all root scope requirements
          2. has sufficient consents for all dependent scope requirements (determined
             by a call to Auth Consents API)
        """
        # client identities are always logged in
        if is_client_login():
            return True

        tokens = self._token_storage.get_token_data(resource_server)
        if tokens is None or "refresh_token" not in tokens:
            return False

        return self._tokens_meet_auth_requirements(
            resource_server, tokens
        ) and self._validate_token(tokens["refresh_token"])

    def _tokens_meet_auth_requirements(
        self, resource_server: str, tokens: dict[str, t.Any]
    ) -> bool:
        return self._tokens_meet_static_requirements(
            resource_server, tokens
        ) and self._tokens_meet_nonstatic_requirements(resource_server, tokens)

    def _tokens_meet_static_requirements(
        self, resource_server: str, tokens: dict[str, t.Any]
    ) -> bool:
        if resource_server not in CLI_SCOPE_REQUIREMENTS.resource_servers():
            # By definition, if there are no requirements, those requirements are met.
            return True

        requirements = CLI_SCOPE_REQUIREMENTS.get_by_resource_server(resource_server)

        # evaluate scope contract version requirements for this service

        # first, fetch the version data and if it is missing, treat it as empty
        contract_versions = read_well_known_config("scope_contract_versions") or {}
        # determine which version we need, and compare against the version in
        # storage with a default of 0
        # if the comparison fails, reject the token as not a valid login for the
        # service
        version_required = requirements["min_contract_version"]
        if contract_versions.get(resource_server, 0) < version_required:
            return False

        token_scopes = set(tokens["scope"].split(" "))
        required_scopes: set[str] = set()
        for scope in requirements["scopes"]:
            if isinstance(scope, str):
                required_scopes.add(scope)
            else:
                required_scopes.add(scope.scope_string)
        return required_scopes - token_scopes == set()

    def _tokens_meet_nonstatic_requirements(
        self, resource_server: str, tokens: dict[str, t.Any]
    ) -> bool:
        if resource_server not in self._nonstatic_requirements:
            # By definition, if there are no requirements, those requirements are met.
            return True

        requirements = self._nonstatic_requirements[resource_server]

        # Parse the requirements into a list of Scope objects
        # This may expand the list of requirements if, for instance, a single scope
        #   string represents multiple roots (eg "openid profile email")
        required_scopes: list[Scope] = []
        for scope in requirements:
            scope_string = scope if isinstance(scope, str) else str(scope)
            required_scopes.extend(Scope.parse(scope_string=scope_string))

        if not any(scope.dependencies for scope in required_scopes):
            # If there are no dependent scopes, simply verify local scope strings match
            required_scope_strings = {scope.scope_string for scope in required_scopes}

            token_scope_strings = set(tokens["scope"].split(" "))
            return required_scope_strings - token_scope_strings == set()
        else:
            # If there are dependent scopes all required scope paths are present in the
            #   user's cached consent forest.
            return self._cached_consent_forest.meets_scope_requirements(required_scopes)

    @property
    @functools.lru_cache(maxsize=1)  # noqa: B019
    def _cached_consent_forest(self) -> ConsentForest:
        identity_id = get_current_identity_id()

        return self.get_auth_client().get_consents(identity_id).to_forest()

    def run_login_flow(
        self,
        *,
        no_local_server: bool = False,
        local_server_message: str | None = None,
        epilog: str | None = None,
        session_params: dict[str, str] | None = None,
        scopes: list[str | MutableScope] | None = None,
    ) -> None:
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

    def assert_logins(
        self,
        *resource_servers: str,
        login_context: LoginContext | None = None,
    ) -> None:
        """
        Verify all registered root & dependent scopes requirements are met for the given
          resource servers.

        :param resource_servers: a list of resource servers to check for logins
        :param login_context: an optional LoginContext object to use for
          custom formatting of error messaging. If omitted, default error messaging
          will be used instead.
        :raises: a MissingLoginError if any root or dependent scope requirements in the
          given resource servers are not met.
        """
        login_context = login_context or LoginContext()

        # Determine the set of resource servers still requiring logins.
        missing_servers = {s for s in resource_servers if not self.has_login(s)}

        # If any resource servers do require logins, raise those as a MissingLoginError.
        if missing_servers:
            raise MissingLoginError(list(missing_servers), login_context)

    @classmethod
    def requires_login(
        cls, *services: ServiceNameLiteral
    ) -> t.Callable[[t.Callable[Concatenate[LoginManager, P], R]], t.Callable[P, R]]:
        """
        Command decorator for specifying a resource server that the user must have
        tokens for in order to run the command.

        Simple usage for commands that have static resource needs: simply list all
        needed services as args. Services should be referred to by "short names":

        @LoginManager.requires_login("auth")

        @LoginManager.requires_login("auth", "transfer")

        Usage for commands which have dynamic resource servers depending
        on the arguments passed to the command (e.g. commands for the GCS API)

        @LoginManager.requires_login()
        def command(login_manager, endpoint_id)

            login_manager.<do the thing>(endpoint_id)
        """
        resource_servers = [
            (
                rs_name
                if rs_name not in CLI_SCOPE_REQUIREMENTS
                else CLI_SCOPE_REQUIREMENTS[rs_name]["resource_server"]
            )
            for rs_name in services
        ]

        def inner(
            func: t.Callable[Concatenate[LoginManager, P], R]
        ) -> t.Callable[P, R]:
            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                manager = cls()
                manager.assert_logins(*resource_servers)
                return func(manager, *args, **kwargs)

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
            if tokens and self._tokens_meet_auth_requirements(resource_server, tokens):
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
        authorizer = self._get_client_authorizer(TimersScopes.resource_server)
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
            epish.assert_entity_type(EntityType.GCSV5_ENDPOINT)
            resolved_ep_id = str(endpoint_id)
        else:  # pragma: no cover
            raise ValueError("Internal Error! collection_id or endpoint_id is required")
        return resolved_ep_id, epish

    def get_specific_flow_client(
        self,
        flow_id: uuid.UUID,
    ) -> globus_sdk.SpecificFlowClient:
        # Create a SpecificFlowClient without an authorizer
        # to take advantage of its scope creation code.
        client = globus_sdk.SpecificFlowClient(flow_id, app_name=version.app_name)
        assert client.scopes is not None
        self.add_requirement(client.scopes.resource_server, [client.scopes.user])

        login_context = LoginContext(
            login_command=f"globus login --flow {flow_id}",
            error_message="Missing 'user' consent for a flow.",
        )
        self.assert_logins(client.scopes.resource_server, login_context=login_context)

        # Create and assign an authorizer now that scope requirements are registered.
        client.authorizer = self._get_client_authorizer(
            client.scopes.resource_server,
            no_tokens_msg=(
                f"Could not get login data for flow {flow_id}. "
                f"Try login with '--flow {flow_id}' to fix."
            ),
        )
        return client

    def get_gcs_client(
        self,
        *,
        collection_id: uuid.UUID | None = None,
        endpoint_id: uuid.UUID | None = None,
        include_data_access: bool = False,
        assert_entity_type: tuple[EntityType] | None = None,
    ) -> CustomGCSClient:
        """
        Retrieve a gcs client for either a collection or an endpoint.

        If a user is determined to not have the required consents for the collection or
          endpoint, raises a MissingLoginError which includes instructions for
          obtaining the required consents.

        :param collection_id: UUID of a mapped or guest collection
        :param endpoint_id: UUID of a GCSv5 endpoint
        :param include_data_access: Whether to include the data_access scope as a
          required dependency if the collection is determined to require it.
        :param assert_entity_type: An optional tuple of expected entity types. If
          supplied & the entity type does not match, raises a WrongEntityTypeError.
        """
        from ..services.gcs import CustomGCSClient

        gcs_id, epish = self._get_gcs_info(
            collection_id=collection_id, endpoint_id=endpoint_id
        )
        if assert_entity_type is not None:
            epish.assert_entity_type(expect_types=assert_entity_type)
        include_data_access = include_data_access and epish.requires_data_access_scope

        if not include_data_access:
            # Just require an endpoint:manage_collections scope
            scope = GCSEndpointScopeBuilder(gcs_id).make_mutable("manage_collections")
            login_context = LoginContext(
                login_command=f"globus login --gcs {gcs_id}",
                error_message="Missing 'manage_collections' consent on an endpoint.",
            )
        else:
            # Require an endpoint:manage_collections scope with a dependent
            #   collection[data_access] scope
            scope = GCSEndpointScopeBuilder(gcs_id).make_mutable("manage_collections")
            data_access = GCSCollectionScopeBuilder(str(collection_id)).data_access
            scope.add_dependency(data_access)

            login_context = LoginContext(
                login_command=f"globus login --gcs {gcs_id}:{str(collection_id)}",
                error_message="Missing 'data_access' consent on a mapped collection.",
            )

        self.add_requirement(gcs_id, scopes=[scope])
        self.assert_logins(gcs_id, login_context=login_context)

        authorizer = self._get_client_authorizer(
            gcs_id,
            no_tokens_msg=(
                f"{login_context.error_message}\n"
                f"Please run:\n\n  {login_context.login_command}\n"
            ),
        )
        return CustomGCSClient(
            epish.get_gcs_address(),
            source_epish=epish,
            authorizer=authorizer,
            app_name=version.app_name,
        )
