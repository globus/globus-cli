"""
A wrapper which nicely integrates SDK IdentityMaps into the CLI.

This was originally implemented in gcs-cli and ported into here.

A "resolver" is defined with a field it uses in each item from the response data as the
full principal value. This is the "key".
Typical usage should be to define a resolver in each command which needs resolution, to
provide the key to use. Definition may have to happen outside of a command to
accommodate field lists which are defined as constants, and this is supported.

A resolver provides a field handler for principal URNs + a pagination callback to get
all principals from each page of results added to the ID map.
It can also be initialized to take identity IDs (not in Principal URN format).

This lets us get some of the benefit of the IdentityMap bulk calls without forcing the
whole paginated call to be walked at once.

This also lets us keep the resolution work only in the text-mode printed output (and not
applied on JSON output).
"""
from __future__ import annotations

import typing as t

import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.types import DATA_CONTAINER_T

IDENTITY_URN_PREFIX = "urn:globus:auth:identity:"


class InvalidPrincipalError(ValueError):
    def __init__(self, value: str) -> None:
        self.value = value


# TODO: work out how to rephrase PrincipalResolver as a FieldFormatter
# this is non-trivial for two reasons:
#
# 1. a FieldFormatter only handles a string to format; note how PrincipalResolver
#    fails over to using the "original" value
# 2. PrincipalResolver uses page_callback to run logic on each page of results,
#    prepopulating the id_map. This is an important optimization because it results in
#    batched lookups against get_identities, rather than a network call per value
#
# page_callback may become a function of the Field objects, to pass pages of results to
# their formatters. This would cover (2).
# (1) is more difficult because it requires a more complex protocol/interface between
# the FieldFormatter and the Field object.
class PrincipalResolver:
    """
    Everything is done lazily via properties so that nothing happens during
    start up.

    Pass ``PrincipalResolver.field`` as a field key for output printing

    Pass ``PrincipalResolver.page_callback`` as a page callback for output printing.

    Usage:

    >>> PrincipalResolver("urnfield")

    creates a resolver which pulls principal URNs from the field named "urnfield"

    >>> PrincipalResolver("idfield", use_urns=False)

    creates a resolver which pulls Identity IDs from the field named "idfield"
    """

    def __init__(self, key: str, use_urns: bool = True) -> None:
        self.key = key
        self.use_urns = use_urns
        self._idmap: globus_sdk.IdentityMap | None = None

    @property
    def idmap(self) -> globus_sdk.IdentityMap:
        if not self._idmap:
            self._idmap = globus_sdk.IdentityMap(LoginManager().get_auth_client())
        return self._idmap

    def _raw_id_from_object(self, obj: DATA_CONTAINER_T) -> tuple[str, str]:
        """
        returns a pair, (original, value)

        can raise InvalidPrincipalError if the input is malformed
        """
        value: str = obj[self.key]
        # if not using URNs, the "raw ID" is just the value and it "always works"
        if not self.use_urns:
            return (value, value)

        # otherwise, check
        # if it doesn't have the URN prefix, it is not a valid URN, so this lookup
        # failed -- the result is (False, ...) to indicate failure
        if not value.startswith(IDENTITY_URN_PREFIX):
            raise InvalidPrincipalError(value)
        # if it has the right prefix, left-strip the prefix as the new value, return the
        # original and the success indicator
        return (value, value[len(IDENTITY_URN_PREFIX) :])

    def field(self, data: DATA_CONTAINER_T) -> str:
        try:
            original, value = self._raw_id_from_object(data)
        except InvalidPrincipalError as err:
            return err.value
        # try to do the lookup and get the "username" property
        # but default to the original value if this doesn't resolve
        return t.cast(str, self.idmap.get(value, {}).get("username", original))

    # TODO: In gcs-cli, page_callback is suported by the pretty printer. In globus-cli,
    # we should attach this to the PagingWrapper. The purpose is to get the map
    # populated on a per-page basis.
    def page_callback(self, data_page: t.Iterable[DATA_CONTAINER_T]) -> None:
        for item in data_page:
            try:
                _original, value = self._raw_id_from_object(item)
            except InvalidPrincipalError:
                continue

            self.idmap.add(value)


default_principal_resolver = PrincipalResolver("principal")
default_identity_id_resolver = PrincipalResolver("identity_id", use_urns=False)
