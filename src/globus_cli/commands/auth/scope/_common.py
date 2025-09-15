from __future__ import annotations

import globus_sdk

from globus_cli.termio import Field, formatters

SCOPE_SUMMARY_FIELDS = [
    Field("Scope ID", "scope"),
    Field("Optional", "optional", formatter=formatters.Bool),
    Field(
        "Requires Refresh Token", "requires_refresh_token", formatter=formatters.Bool
    ),
]

DECORATED_SCOPE_SUMMARY_FIELDS = [
    # Scope summaries don't actually contain a "scope_string" field
    # But it's very useful to understanding a dependent scope, so we decorate it in.
    Field("Scope String", "scope_string"),
] + SCOPE_SUMMARY_FIELDS

_BASE_SCOPE_FIELDS = [
    Field("Scope String", "scope_string"),
    Field("Scope ID", "id"),
    Field("Name", "name"),
    Field("Description", "description", wrap_enabled=True),
    Field("Client ID", "client"),
    Field("Allows Refresh Tokens", "allows_refresh_token", formatter=formatters.Bool),
    Field("Required Domains", "required_domains", formatter=formatters.Array),
    Field("Advertised", "advertised", formatter=formatters.Bool),
]

DECORATED_SCOPE_FIELDS = _BASE_SCOPE_FIELDS + [
    Field(
        "Dependent Scopes",
        "dependent_scopes",
        formatter=formatters.ArrayMultilineFormatter(
            formatters.RecordFormatter(DECORATED_SCOPE_SUMMARY_FIELDS)
        ),
    ),
]


class BatchScopeStringResolver:
    """
    A resolver for accessing multiple scope strings without making multiple requests.

    The list of scopes ids, provided at initialization, are queried in a batch request
    and cached for future access once the first scope string is resolved.

    :param auth_client: The AuthClient to use for scope string resolution.
    :param scope_ids: A list of scope IDs to resolve.
    :param default: A default string to return in case a scope id couldn't be found.
    """

    def __init__(
        self,
        auth_client: globus_sdk.AuthClient,
        scope_ids: list[str],
        default: str | None = "UNKNOWN",
    ) -> None:
        self._auth_client = auth_client
        self._scope_ids = scope_ids
        self._scope_strings: dict[str, str] | None = None
        self._default = default

    def resolve(self, scope_id: str) -> str:
        if scope_id not in self._scope_ids:
            raise ValueError(f"Scope ID {scope_id} was not registered for resolution.")
        elif scope_id not in self.scope_strings:
            if self._default is not None:
                return self._default
            raise ValueError(f"Scope string for {scope_id} could not be retrieved.")
        return self.scope_strings[scope_id]

    @property
    def scope_strings(self) -> dict[str, str]:
        """A mapping of scope ID to their scope strings."""
        if self._scope_strings is None:
            resp = self._auth_client.get_scopes(ids=self._scope_ids)
            self._scope_strings = {
                scope["id"]: scope["scope_string"] for scope in resp.get("scopes", [])
            }
        return self._scope_strings
