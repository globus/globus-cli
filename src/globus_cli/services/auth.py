from __future__ import annotations

import typing as t
import uuid

import globus_sdk
import globus_sdk.scopes


def _is_uuid(s):
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False


class CustomAuthClient(globus_sdk.AuthClient):
    def _lookup_identity_field(
        self, id_name=None, id_id=None, field="id", provision=False
    ):
        assert (id_name or id_id) and not (id_name and id_id)

        kw = dict(provision=provision)
        if id_name:
            kw.update({"usernames": id_name})
        else:
            kw.update({"ids": id_id})

        try:
            return self.get_identities(**kw)["identities"][0][field]
        except (IndexError, KeyError):
            # IndexError: identity does not exist and wasn't provisioned
            # KeyError: `field` does not exist for the requested identity
            return None

    def maybe_lookup_identity_id(self, identity_name, provision=False):
        if _is_uuid(identity_name):
            return identity_name
        else:
            return self._lookup_identity_field(
                id_name=identity_name, provision=provision
            )

    def lookup_identity_name(self, identity_id):
        return self._lookup_identity_field(id_id=identity_id, field="username")

    def get_consents(self, identity_id) -> ConsentForestResponse:
        """
        Get the consent for a given identity_id
        """
        return ConsentForestResponse(
            self.get(f"/v2/api/identities/{identity_id}/consents")
        )


class ConsentForestResponse(globus_sdk.GlobusHTTPResponse):
    @property
    def consents(self) -> list[dict[str, t.Any]]:
        return t.cast("list[dict[str, t.Any]]", self.data["consents"])

    def top_level_consents(self) -> list[dict[str, t.Any]]:
        return [c for c in self.consents if len(c["dependency_path"]) == 1]

    def get_child_consents(self, consent: dict[str, t.Any]) -> list[dict[str, t.Any]]:
        path_length = len(consent["dependency_path"]) + 1
        return [
            c
            for c in self.consents
            if len(c["dependency_path"]) == path_length
            and c["dependency_path"][:-1] == consent["dependency_path"]
        ]

    def contains_scopes(
        self, scope_trees: list[globus_sdk.scopes.MutableScope]
    ) -> bool:
        """
        Determine whether or not a user's consents contains the given scope trees.
        """
        top_level_by_name = _map_consents_by_name(self.top_level_consents())

        for scope in scope_trees:
            if scope.scope_string not in top_level_by_name:
                return False

        trees_to_match = [
            (
                top_level_by_name[s.scope_string],
                s,
            )
            for s in scope_trees
        ]

        while trees_to_match:
            consent, scope = trees_to_match.pop()
            child_consents = _map_consents_by_name(self.get_child_consents(consent))
            for dependency in scope.dependencies:
                if dependency.scope_string not in child_consents:
                    return False
                trees_to_match.append(
                    (child_consents[dependency.scope_string], dependency)
                )
        return True


def _map_consents_by_name(
    consents: list[dict[str, t.Any]]
) -> dict[str, dict[str, t.Any]]:
    return {c["scope_name"]: c for c in consents}
