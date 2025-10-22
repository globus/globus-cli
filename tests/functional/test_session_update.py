import uuid

import pytest


def test_username_not_in_idset(run_line, userinfo_mocker):
    """trying to 'session update' with an identity not in your identity set results in
    an error"""
    userinfo_mocker.configure_unlinked(username="geordi@ncc1701d.starfleet")
    result = run_line("globus session update ro@ncc1701d.starfleet", assert_exit_code=1)
    assert "'ro@ncc1701d.starfleet' is not in your identity set" in result.stderr


@pytest.mark.parametrize("userparam", ["ro@ncc1701d.starfleet", str(uuid.UUID(int=10))])
def test_mix_user_and_domains(run_line, userinfo_mocker, userparam):
    userinfo_mocker.configure_unlinked(username="geordi@ncc1701d.starfleet")
    result = run_line("globus session update ro@ncc1701d.starfleet", assert_exit_code=1)
    result = run_line(
        f"globus session update uchicago.edu {userparam}", assert_exit_code=2
    )
    assert (
        "domain-type identities and user-type identities are mutually exclusive"
        in result.stderr
    )


@pytest.mark.parametrize(
    "idparam",
    ["ro@ncc1701d.starfleet", str(uuid.UUID(int=10)), "uchicago.edu"],
)
def test_all_mutex(run_line, userinfo_mocker, idparam):
    userinfo_mocker.configure_unlinked(username="geordi@ncc1701d.starfleet")
    result = run_line(f"globus session update --all {idparam}", assert_exit_code=2)
    assert (
        "IDENTITY values, --all, and --policy are all mutually exclusive"
        in result.stderr
    )


def test_username_flow(run_line, userinfo_mocker, mock_remote_session, mock_link_flow):
    mock_remote_session.return_value = True

    meta = userinfo_mocker.configure_unlinked().metadata
    username = meta["username"]
    user_id = meta["sub"]

    result = run_line(f"globus session update {username}")

    assert "You have successfully updated your CLI session." in result.output

    mock_link_flow.assert_called_once()
    _call_args, call_kwargs = mock_link_flow.call_args
    assert "session_params" in call_kwargs
    assert "session_required_identities" in call_kwargs["session_params"]
    assert call_kwargs["session_params"]["session_required_identities"] == user_id


@pytest.mark.parametrize("with_scopes", [True, False])
def test_domain_flow(
    run_line, userinfo_mocker, mock_remote_session, mock_link_flow, with_scopes
):
    mock_remote_session.return_value = True
    userinfo_mocker.configure_unlinked()

    scopes_args = ""
    if with_scopes:
        scopes_args = " --scope urn:globus:auth:scope:example.api:all --scope foo"

    result = run_line(f"globus session update uchicago.edu{scopes_args}")

    assert "You have successfully updated your CLI session." in result.output

    mock_link_flow.assert_called_once()
    _call_args, call_kwargs = mock_link_flow.call_args
    assert "session_params" in call_kwargs
    assert "session_required_single_domain" in call_kwargs["session_params"]
    assert (
        call_kwargs["session_params"]["session_required_single_domain"]
        == "uchicago.edu"
    )


@pytest.mark.parametrize("with_scopes", [True, False])
def test_all_flow(
    run_line, userinfo_mocker, mock_remote_session, mock_local_server_flow, with_scopes
):
    mock_remote_session.return_value = False
    meta = userinfo_mocker.configure(
        {"username": "data@ncc1701d.starfleet"},
        [{"username": "lore@ncc1701d.starfleet"}],
    ).metadata

    ids = [x["sub"] for x in meta["identity_set"]]

    scopes_args = ""
    if with_scopes:
        scopes_args = " --scope urn:globus:auth:scope:example.api:all --scope foo"

    result = run_line(f"globus session update --all{scopes_args}")

    assert "You have successfully updated your CLI session." in result.output

    mock_local_server_flow.assert_called_once()
    _call_args, call_kwargs = mock_local_server_flow.call_args
    assert "session_params" in call_kwargs
    assert "session_required_identities" in call_kwargs["session_params"]
    assert set(
        call_kwargs["session_params"]["session_required_identities"].split(",")
    ) == set(ids)


@pytest.mark.parametrize("with_scopes", [True, False])
def test_policy_flow(
    run_line, userinfo_mocker, mock_remote_session, mock_link_flow, with_scopes
):
    mock_remote_session.return_value = True
    userinfo_mocker.configure_unlinked()

    scopes_args = ""
    if with_scopes:
        scopes_args = " --scope urn:globus:auth:scope:example.api:all --scope foo"

    result = run_line(f"globus session update --policy foo,bar{scopes_args}")

    assert "You have successfully updated your CLI session." in result.output

    mock_link_flow.assert_called_once()
    _call_args, call_kwargs = mock_link_flow.call_args
    assert "session_params" in call_kwargs
    assert "session_required_policies" in call_kwargs["session_params"]
    assert call_kwargs["session_params"]["session_required_policies"] == "foo,bar"
