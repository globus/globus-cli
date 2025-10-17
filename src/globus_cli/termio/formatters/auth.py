from __future__ import annotations

import abc
import typing as t

import globus_sdk

from .base import FieldFormatter

_IDENTITY_URN_PREFIX = "urn:globus:auth:identity:"
_GROUP_URN_PREFIX = "urn:globus:groups:id:"


class PrincipalFormatter(FieldFormatter[t.Tuple[str, str]]):
    """
    PrincipalFormatters work over (principal, type) tuples.

    a "principal" could be an identity ID, a group ID, an identity URN, or a
        special-cased value

    a "type" is typically a well-known string which instructs the formatter how to
        do rendering like "group" or "identity"

    The base class defines three rendering cases:
      - identity
      - group
      - fallback
    """

    def __init__(self, auth_client: globus_sdk.AuthClient) -> None:
        self.auth_client = auth_client
        self.resolved_ids = globus_sdk.IdentityMap(auth_client)

    def render_identity_id(self, identity_id: str) -> str:
        try:
            return t.cast(str, self.resolved_ids[identity_id]["username"])
        except LookupError:
            return identity_id

    # TODO: re-assess Group rendering in the CLI
    # see also: any overrides for this function for other formatters
    def render_group_id(self, group_id: str) -> str:
        return f"Globus Group ({group_id})"

    def fallback_rendering(self, principal: str, principal_type: str) -> str:
        return principal

    # the base PrincipalFormatter cannot be instantiated because parse() is variable
    # by the exact type of data being read
    @abc.abstractmethod
    def parse(self, value: t.Any) -> tuple[str, str]: ...

    def add_item(self, value: t.Any) -> None:
        """
        TODO - is this correct?
        Register a principal on the formatter, making it eligible for resolution.
        """
        try:
            principal, principal_type = self.parse(value)
        except ValueError:
            pass
        else:
            if principal_type == "identity":
                self.resolved_ids.add(principal)

    def render(self, value: tuple[str, str]) -> str:
        principal, principal_type = value

        if principal_type == "identity":
            return self.render_identity_id(principal)
        elif principal_type == "group":
            return self.render_group_id(principal)
        else:
            return self.fallback_rendering(principal, principal_type)


class IdentityIDFormatter(PrincipalFormatter):
    def parse(self, value: t.Any) -> tuple[str, str]:
        if not isinstance(value, str):
            raise ValueError("non-str identity value")
        return (value, "identity")


class PrincipalURNFormatter(PrincipalFormatter):
    def parse(self, value: t.Any) -> tuple[str, str]:
        if not isinstance(value, str):
            raise ValueError("non-str principal URN value")
        if value.startswith(_IDENTITY_URN_PREFIX):
            return (value[len(_IDENTITY_URN_PREFIX) :], "identity")
        if value.startswith(_GROUP_URN_PREFIX):
            return (value[len(_GROUP_URN_PREFIX) :], "group")
        return (value, "fallback")


class PrincipalDictFormatter(PrincipalFormatter):
    def parse(self, value: t.Any) -> tuple[str, str]:
        if isinstance(value, globus_sdk.GlobusHTTPResponse):
            value = value.data
        if not isinstance(value, dict):
            raise ValueError("cannot format principal from non-dict data")

        principal = t.cast(str, value["principal"])
        principal_type = t.cast(str, value["principal_type"])
        if principal_type in ("identity", "group"):
            return (principal, principal_type)
        return (principal, "fallback")
