import uuid

from globus_sdk.testing import RegisteredResponse


class UserinfoMocker:
    """A utility for setting up `GET /v2/oauth2/userinfo` mocks."""

    _DEFAULT_IDP_ID = str(uuid.uuid4())
    _DEFAULT_IDENTITY_ID = str(uuid.uuid4())

    def configure_unlinked(
        self,
        username="shrek@globus.org",
        name="Shrek by William Steig",
        email="shrek+contactme@globus.org",
        organization=(
            "Fairytales Whose Movie Adaptations Diverge "
            "Significantly From Their Source Material"
        ),
        identity_provider_display_name="Globus IDP",
        status="used",
        identity_provider=_DEFAULT_IDP_ID,
        sub=_DEFAULT_IDENTITY_ID,
    ):
        """Setup a single-identity mock where the primary info matches the only
        identity in the identity set."""
        identity_doc = {
            "email": email,
            "identity_provider": identity_provider,
            "identity_provider_display_name": identity_provider_display_name,
            "name": name,
            "organization": organization,
            "status": status,
            "sub": sub,
            "username": username,
        }
        return self.configure(identity_doc, add_metadata=identity_doc)

    def configure(self, primary_info, identity_set_partials=(), *, add_metadata=None):
        """Configure a mock with primary user info and however many partials
        were given for linked identities.

        Example usage:

        >>> mocker.configure(
        >>>     {"username": "foo@globusid.org", "sub": my_coordinated_id1},
        >>>     [
        >>>         {"username": "bar@globusid.org", "sub": my_coordinated_id2},
        >>>         {"username": "baz@globusid.org"},
        >>>     ]
        >>> )
        """
        primary_doc = {
            "email": primary_info.get("email", "primary+contacme@globus.org"),
            "name": primary_info.get("name", "Primary Identity"),
            "preferred_username": primary_info.get("username", "primary@globus.org"),
            "sub": primary_info.get("sub", str(uuid.uuid4())),
        }

        identity_set = []
        for n, partial in enumerate([primary_info, *identity_set_partials]):
            identity_set.append(
                {
                    "email": partial.get("email", f"clone{n}+contacme@globus.org"),
                    "identity_provider": partial.get(
                        "identity_provider", self._DEFAULT_IDP_ID
                    ),
                    "identity_provider_display_name": partial.get(
                        "identity_provider_display_name", "Globus IDP"
                    ),
                    "name": partial.get("name", f"Clone {n}"),
                    "organization": partial.get(
                        "organization", "Globus Cloning Intergalactic"
                    ),
                    "status": partial.get("status", "used"),
                    "sub": partial.get("sub", str(uuid.uuid4())),
                    "username": partial.get("username", f"clone{n}@globus.org"),
                }
            )

        resp = RegisteredResponse(
            service="auth",
            path="/v2/oauth2/userinfo",
            json={**primary_doc, "identity_set": identity_set},
            metadata={
                "identity_set": identity_set,
                "primary_doc": primary_doc,
                **(add_metadata or {}),
            },
        )

        resp.add()

        return resp
