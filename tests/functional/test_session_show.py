import datetime
import uuid

import pytest
from globus_sdk.testing import load_response_set, register_response_set


class utconly_datetime(datetime.datetime):
    def astimezone(self, tz=None):
        return super().astimezone(tz=datetime.timezone.utc)


@pytest.fixture(autouse=True, scope="session")
def setup_session():
    user_attrs = {
        "username": "cthulhu@rlyeh",
        "name": "Cthulhu",
        "email": "dead-cthulhu-waits-dreaming@globus.org",
        "id": str(uuid.uuid4()),
        "identity_provider": str(uuid.uuid4()),
        "organization": "Point Nemo",
    }
    auth_time = "1989-06-07 10:11 UTC"
    register_response_set(
        "cthulhu_introspect",
        {
            "introspect": {
                "service": "auth",
                "path": "/v2/oauth2/token/introspect",
                "method": "POST",
                "json": create_introspect_data(user_attrs, auth_time=auth_time),
            },
        },
        metadata={"user_attrs": user_attrs, "auth_time": auth_time},
    )


def create_introspect_data(user_attrs, auth_time):
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
                    "idp": user_attrs["identity_provider"],
                    "auth_time": datetime.datetime.strptime(
                        auth_time, "%Y-%m-%d %H:%M %Z"
                    )
                    .replace(tzinfo=datetime.timezone.utc)
                    .timestamp(),
                    "custom_claims": {},
                }
            },
        },
    }


def test_session_show_text(run_line, monkeypatch, get_identities_mocker):
    meta = load_response_set("cthulhu_introspect").metadata
    get_identities_mocker.configure_one(**meta["user_attrs"])

    monkeypatch.setattr(datetime, "datetime", utconly_datetime)

    result = run_line("globus session show")

    lines = result.output.split("\n")
    # header, spacer, one line of content, trailing newline -> 4 lines
    assert len(lines) == 4
    assert lines[-1] == ""
    lines = lines[:-1]
    content_row = [x.strip() for x in lines[-1].split("|")]
    assert len(content_row) == 3  # 3 columns
    assert content_row[0] == meta["user_attrs"]["username"]
    assert content_row[1] == meta["user_attrs"]["id"]
    assert content_row[2] == meta["auth_time"]
