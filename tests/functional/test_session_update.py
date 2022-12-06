import pytest
from globus_sdk._testing import load_response_set


def test_username_not_in_idset(run_line):
    """trying to 'session update' with an identity not in your identity set results in
    an error"""
    load_response_set("cli.foo_user_info")
    result = run_line("globus session update sirosen@globusid.org", assert_exit_code=1)
    assert "'sirosen@globusid.org' is not in your identity set" in result.stderr


@pytest.mark.parametrize(
    "userparam", ["sirosen@globusid.org", "f4ee724c-b27c-4ccc-8237-989aa4085af4"]
)
def test_mix_user_and_domains(run_line, userparam):
    load_response_set("cli.foo_user_info")
    result = run_line(
        f"globus session update uchicago.edu {userparam}", assert_exit_code=2
    )
    assert (
        "domain-type identities and user-type identities are mutually exclusive"
        in result.stderr
    )


@pytest.mark.parametrize(
    "idparam",
    ["sirosen@globusid.org", "f4ee724c-b27c-4ccc-8237-989aa4085af4", "uchicago.edu"],
)
def test_all_mutex(run_line, idparam):
    load_response_set("cli.foo_user_info")
    result = run_line(f"globus session update --all {idparam}", assert_exit_code=2)
    assert (
        "IDENTITY values, --all, and --policy are all mutually exclusive"
        in result.stderr
    )


def test_username_flow(run_line, mock_remote_session, mock_link_flow):
    mock_remote_session.return_value = True

    meta = load_response_set("cli.foo_user_info").metadata
    username = meta["username"]
    user_id = meta["user_id"]

    result = run_line(f"globus session update {username}")

    assert "You have successfully updated your CLI session." in result.output

    mock_link_flow.assert_called_once()
    _call_args, call_kwargs = mock_link_flow.call_args
    assert "session_params" in call_kwargs
    assert "session_required_identities" in call_kwargs["session_params"]
    assert call_kwargs["session_params"]["session_required_identities"] == user_id


def test_domain_flow(run_line, mock_remote_session, mock_link_flow):
    mock_remote_session.return_value = True

    load_response_set("cli.foo_user_info")

    result = run_line("globus session update uchicago.edu")

    assert "You have successfully updated your CLI session." in result.output

    mock_link_flow.assert_called_once()
    _call_args, call_kwargs = mock_link_flow.call_args
    assert "session_params" in call_kwargs
    assert "session_required_single_domain" in call_kwargs["session_params"]
    assert (
        call_kwargs["session_params"]["session_required_single_domain"]
        == "uchicago.edu"
    )


def test_all_flow(run_line, mock_remote_session, mock_local_server_flow):
    mock_remote_session.return_value = False

    meta = load_response_set("cli.foo_user_info").metadata
    ids = [x["user_id"] for x in meta["linked_ids"]]
    ids.append(meta["user_id"])

    result = run_line("globus session update --all")

    assert "You have successfully updated your CLI session." in result.output

    mock_local_server_flow.assert_called_once()
    _call_args, call_kwargs = mock_local_server_flow.call_args
    assert "session_params" in call_kwargs
    assert "session_required_identities" in call_kwargs["session_params"]
    assert set(
        call_kwargs["session_params"]["session_required_identities"].split(",")
    ) == set(ids)


def test_policy_flow(run_line, mock_remote_session, mock_link_flow):
    mock_remote_session.return_value = True

    load_response_set("cli.foo_user_info")

    result = run_line("globus session update --policy foo,bar")

    assert "You have successfully updated your CLI session." in result.output

    mock_link_flow.assert_called_once()
    _call_args, call_kwargs = mock_link_flow.call_args
    assert "session_params" in call_kwargs
    assert "session_required_policies" in call_kwargs["session_params"]
    assert call_kwargs["session_params"]["session_required_policies"] == "foo,bar"
