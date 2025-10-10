import uuid

from globus_sdk.testing import RegisteredResponse


class GetIdentitiesMocker:
    """A utility for setting up `GET /v2/api/identities` mocks."""

    _DEFAULT_IDP_ID = str(uuid.uuid4())
    _DEFAULT_IDENTITY_ID = str(uuid.uuid4())

    def configure_empty(self):
        return self.configure([])

    def configure_one(
        self,
        username="shrek@globus.org",
        email="shrek+contactme@globus.org",
        name="Shrek by William Steig",
        organization=(
            "Fairytales Whose Movie Adaptations Diverge "
            "Significantly From Their Source Material"
        ),
        status="used",
        identity_provider=_DEFAULT_IDP_ID,
        id=_DEFAULT_IDENTITY_ID,
    ):
        """Setup a single-identity mock."""
        identity_doc = {
            "email": email,
            "id": id,
            "identity_provider": identity_provider,
            "name": name,
            "organization": organization,
            "status": status,
            "username": username,
        }
        return self.configure([identity_doc], add_metadata=identity_doc)

    def configure(self, partial_documents, *, add_metadata=None):
        """Configure a mock with however many partials were given.

        Example usage:

        >>> mocker.configure(
        >>>     [
        >>>         {"username": "foo@globusid.org", "id": my_coordinated_id1},
        >>>         {"username": "bar@globusid.org", "id": my_coordinated_id2},
        >>>         {"username": "baz@globusid.org"},
        >>>     ]
        >>> )
        """

        user_docs = []
        for n, partial in enumerate(partial_documents):
            user_docs.append(
                {
                    "id": partial.get("id", str(uuid.uuid4())),
                    "identity_provider": partial.get(
                        "identity_provider", self._DEFAULT_IDP_ID
                    ),
                    "organization": partial.get(
                        "organization", "Globus Cloning Intergalactic"
                    ),
                    "status": partial.get("status", "used"),
                    "email": partial.get("email", f"clone{n}+contactme@globus.org"),
                    "name": partial.get("name", f"Clone {n}"),
                    "username": partial.get("username", f"clone{n}@globus.org"),
                }
            )

        resp = RegisteredResponse(
            service="auth",
            path="/v2/api/identities",
            json={"identities": user_docs},
            metadata={
                "user_docs": user_docs,
                **(add_metadata or {}),
            },
        )

        resp.add()

        return resp
