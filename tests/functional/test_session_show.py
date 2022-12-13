import datetime
import uuid

import pytest
from globus_sdk._testing import load_response_set, register_response_set


class utconly_datetime(datetime.datetime):
    def astimezone(self, tz=None):
        return super().astimezone(tz=datetime.timezone.utc)


@pytest.fixture(autouse=True, scope="session")
def _register_session_introspect_response():
    cthulhu_user_attrs = {
        "username": "cthulhu@rlyeh",
        "name": "Cthulhu",
        "email": "dead-cthulhu-waits-dreaming@globus.org",
        "id": str(uuid.uuid4()),
        "idp_id": str(uuid.uuid4()),
        "auth_time": "1989-06-07 10:11 UTC",
    }

    register_response_set(
        "cthulhu_session",
        dict(
            introspect=dict(
                service="auth",
                path="/v2/oauth2/token/introspect",
                method="POST",
                json=create_introspect_data(cthulhu_user_attrs),
            ),
            identities=dict(
                service="auth",
                path="/v2/api/identities",
                json={
                    "identities": [
                        {
                            "username": cthulhu_user_attrs["username"],
                            "name": cthulhu_user_attrs["name"],
                            "id": cthulhu_user_attrs["id"],
                            "identity_provider": cthulhu_user_attrs["idp_id"],
                            "organization": "Point Nemo",
                            "status": "used",
                            "email": cthulhu_user_attrs["email"],
                        }
                    ]
                },
            ),
        ),
        metadata=cthulhu_user_attrs,
    )


def create_introspect_data(user_attrs):
    # NB: this is supposed to match the client ID for the generated CLI client
    # however, nothing checks it today
    # revisit if we add checks to our commands for this, as we'll need to ensure that
    # it matches stored data
    client_id = str(uuid.uuid4())

    return {
        "active": True,
        "token_type": "Bearer",
        "scope": (
            "openid profile "
            "urn:globus:auth:scope:auth.globus.org:view_identity_set "
            "email"
        ),
        "client_id": client_id,
        "username": user_attrs["username"],
        "name": user_attrs["name"],
        "email": user_attrs["email"],
        "exp": 1670449072,
        "iat": 1670276272,
        "nbf": 1670276272,
        "sub": user_attrs["id"],
        "aud": ["auth.globus.org", client_id],
        "iss": "https://auth.globus.org",
        "session_info": {
            "session_id": str(uuid.uuid4()),
            "authentications": {
                user_attrs["id"]: {
                    "acr": None,
                    "amr": None,
                    "idp": user_attrs["idp_id"],
                    "auth_time": datetime.datetime.strptime(
                        user_attrs["auth_time"], "%Y-%m-%d %H:%M %Z"
                    )
                    .replace(tzinfo=datetime.timezone.utc)
                    .timestamp(),
                    "custom_claims": {},
                }
            },
        },
    }


def test_session_show_text(run_line, monkeypatch):
    meta = load_response_set("cthulhu_session").metadata

    monkeypatch.setattr(datetime, "datetime", utconly_datetime)

    result = run_line("globus session show")

    lines = result.output.split("\n")
    # header, spacer, one line of content, trailing newline -> 4 lines
    assert len(lines) == 4
    assert lines[-1] == ""
    lines = lines[:-1]
    content_row = [x.strip() for x in lines[-1].split("|")]
    assert len(content_row) == 3  # 3 columns
    assert content_row[0] == meta["username"]
    assert content_row[1] == meta["id"]
    assert content_row[2] == meta["auth_time"]
