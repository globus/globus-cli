from __future__ import annotations

import typing as t
import uuid

import globus_sdk
import globus_sdk.scopes


def _is_uuid(s: str) -> bool:
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False


class GetIdentitiesKwargs(t.TypedDict, total=False):
    provision: bool
    usernames: str
    ids: str


class CustomAuthClient(globus_sdk.AuthClient):
    def _lookup_identity_field(
        self,
        id_name: str | None = None,
        id_id: str | None = None,
        field: t.Literal["id", "username"] = "id",
        provision: bool = False,
    ) -> str | None:
        assert (id_name or id_id) and not (id_name and id_id)

        kw: GetIdentitiesKwargs = {"provision": provision}
        if id_name:
            kw["usernames"] = id_name
        elif id_id:
            kw["ids"] = id_id
        else:
            raise NotImplementedError("must provide id or name")

        try:
            value = self.get_identities(**kw)["identities"][0][field]
        # capture any failure to lookup this data, including:
        # - identity doesn't exist (`identities=[]`)
        # - field is missing
        except LookupError:
            return None

        if not isinstance(value, str):
            return None

        return value

    @t.overload
    def maybe_lookup_identity_id(
        self, identity_name: str, provision: t.Literal[True]
    ) -> str: ...

    @t.overload
    def maybe_lookup_identity_id(
        self, identity_name: str, provision: bool = False
    ) -> str | None: ...

    def maybe_lookup_identity_id(
        self, identity_name: str, provision: bool = False
    ) -> str | None:
        if _is_uuid(identity_name):
            return identity_name
        else:
            return self._lookup_identity_field(
                id_name=identity_name, provision=provision
            )

    def lookup_identity_name(self, identity_id: str) -> str | None:
        return self._lookup_identity_field(id_id=identity_id, field="username")
