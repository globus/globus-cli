import json

from globus_sdk._testing import load_response_set


def test_get_identities_requires_at_least_one(run_line):
    result = run_line("globus get-identities", assert_exit_code=2)
    assert "Missing argument" in result.stderr


def test_default_one_id(run_line, get_identities_mocker):
    """
    Runs get-identities with one id, confirms correct username returned.
    """
    meta = get_identities_mocker.configure_one().metadata
    user_id = meta["id"]
    username = meta["username"]
    result = run_line(f"globus get-identities {user_id}")
    assert username + "\n" == result.output


def test_default_one_username(run_line, get_identities_mocker):
    """
    Runs get-identities with one username, confirms correct id returned.
    """
    meta = get_identities_mocker.configure_one().metadata
    user_id = meta["id"]
    username = meta["username"]
    result = run_line("globus get-identities " + username)
    assert user_id + "\n" == result.output


def test_default_nosuchidentity(run_line, get_identities_mocker):
    get_identities_mocker.configure_empty()
    result = run_line("globus get-identities invalid@nosuchdomain.exists")
    assert "NO_SUCH_IDENTITY\n" == result.output


def test_invalid_username(run_line):
    # check that 'invalid' is called out as not being a valid username or identity
    result = run_line("globus get-identities invalid", assert_exit_code=2)
    assert "'invalid' does not appear to be a valid identity" in result.stderr


def test_default_multiple_inputs(run_line):
    """
    Runs get-identities with id username, duplicate and invalid inputs
    Confirms order is preserved and all values are as expected
    """
    meta = load_response_set("cli.multiuser_get_identities").metadata
    users = meta["users"]
    in_vals = [
        users[0]["username"],
        users[0]["user_id"],
        "invalid@nosuchdomain.exists",
        users[1]["username"],
        users[1]["username"],
    ]

    expected = [
        users[0]["user_id"],
        users[0]["username"],
        "NO_SUCH_IDENTITY",
        users[1]["user_id"],
        users[1]["user_id"],
    ]

    result = run_line("globus get-identities " + " ".join(in_vals))
    assert "\n".join(expected) + "\n" == result.output


def test_verbose(run_line, get_identities_mocker):
    """
    Runs get-identities with --verbose, confirms expected fields found.
    """
    meta = get_identities_mocker.configure_one().metadata
    user_id = meta["id"]
    result = run_line("globus get-identities --verbose " + user_id)
    for key in ["username", "id", "name", "organization", "email"]:
        assert meta[key] in result.output


def test_json(run_line, get_identities_mocker):
    """
    Runs get-identities with -F json confirms expected values.
    """
    meta = get_identities_mocker.configure_one().metadata
    user_id = meta["id"]
    output = json.loads(run_line("globus get-identities -F json " + user_id).output)
    for key in ["id", "username", "name", "organization", "email"]:
        assert meta[key] == output["identities"][0][key]
