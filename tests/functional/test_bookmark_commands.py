import json

from globus_sdk.testing import load_response_set


def test_bookmark_create(run_line, go_ep1_id):
    """
    Runs bookmark create, confirms simple things about text and json output.
    """
    meta = load_response_set("cli.bookmark_operations").metadata
    bookmark_id = meta["bookmark_id"]
    result = run_line(f"globus bookmark create {go_ep1_id}:/share/ sharebm")
    assert f"Bookmark ID: {bookmark_id}" in result.output

    # repeat, but with JSON output
    json_output = json.loads(
        run_line(f"globus bookmark create -Fjson {go_ep1_id}:/share/ sharebm").output
    )
    assert json_output["id"] == bookmark_id
    assert json_output["name"] == "sharebm"
    assert json_output["path"] == "/share/"
    assert json_output["endpoint_id"] == go_ep1_id


def test_bookmark_show(run_line, go_ep1_id):
    """
    Runs bookmark show on bm1's name and id.
    Confirms both inputs work, and verbose output is as expected.
    """
    meta = load_response_set("cli.bookmark_operations").metadata
    bookmark_id = meta["bookmark_id"]
    bookmark_name = meta["bookmark_name"]

    # id
    result = run_line(f'globus bookmark show "{bookmark_id}"')
    assert f"{go_ep1_id}:/share/\n" == result.output

    # name
    result = run_line(f'globus bookmark show "{bookmark_name}"')
    assert f"{go_ep1_id}:/share/\n" == result.output

    # verbose
    result = run_line(f"globus bookmark show -v {bookmark_id}")
    assert f"Endpoint ID: {go_ep1_id}" in result.output


def test_bookmark_rename_by_id(run_line):
    """
    Runs bookmark rename on bm1's id.
    """
    meta = load_response_set("cli.bookmark_operations").metadata
    bookmark_id = meta["bookmark_id"]
    updated_bookmark_name = meta["bookmark_name_after_update"]

    result = run_line(
        f'globus bookmark rename "{bookmark_id}" "{updated_bookmark_name}"'
    )
    assert "Success" in result.output


def test_bookmark_rename_by_name(run_line):
    """
    Runs bookmark rename on bm1's name. Confirms can be shown by new name.
    """
    meta = load_response_set("cli.bookmark_operations").metadata
    bookmark_name = meta["bookmark_name"]
    updated_bookmark_name = meta["bookmark_name_after_update"]

    result = run_line(
        f'globus bookmark rename "{bookmark_name}" "{updated_bookmark_name}"'
    )
    assert "Success" in result.output


def test_bookmark_delete_by_id(run_line):
    """
    Runs bookmark delete on bm1's id. Confirms success message.
    """
    meta = load_response_set("cli.bookmark_operations").metadata
    bookmark_id = meta["bookmark_id"]
    result = run_line(f'globus bookmark delete "{bookmark_id}"')
    assert "deleted successfully" in result.output


def test_bookmark_delete_by_name(run_line):
    """
    Runs bookmark delete on bm1's name. Confirms success message.
    """
    meta = load_response_set("cli.bookmark_operations").metadata
    bookmark_name = meta["bookmark_name"]
    result = run_line(f'globus bookmark delete "{bookmark_name}"')
    assert "deleted successfully" in result.output


def test_bookmark_list(run_line):
    meta = load_response_set("cli.bookmark_list").metadata
    bookmarks = meta["bookmarks"]

    result = run_line("globus bookmark list")
    for bm_id in bookmarks.keys():
        assert bm_id in result.output

    lines = result.output.split("\n")
    for bm_id, data in bookmarks.items():
        for line in lines:
            if bm_id not in line:
                continue
            assert data["name"] in line
            assert data["path"] in line
            if data["ep_name"] is not None:
                assert data["ep_name"] in line
            else:
                assert "[DELETED ENDPOINT]" in line
            break


def test_bookmark_list_failure(run_line):
    load_response_set("cli.bookmark_list_failure")
    result = run_line("globus bookmark list", assert_exit_code=1)
    assert "InternalError" in result.stderr
