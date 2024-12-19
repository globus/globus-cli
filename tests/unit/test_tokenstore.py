from globus_cli.login_manager.storage import _resolve_namespace


def test_default_namespace():
    assert _resolve_namespace() == "userprofile/production"


def test_profile_namespace(user_profile):
    assert _resolve_namespace() == "userprofile/production/test_user_profile"


def test_client_namespace(client_login):
    assert _resolve_namespace() == "clientprofile/production/fake_client_id"
