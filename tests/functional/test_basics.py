import os
import re
import uuid

import pytest
from globus_sdk.testing import RegisteredResponse, load_response, load_response_set


def test_parsing(run_line):
    result = run_line("globus --help")
    assert "-h, --help" in result.output
    assert "Show this message and exit." in result.output


def test_command(run_line):
    """
    Runs list-commands and confirms the command is run.
    """
    result = run_line("globus list-commands")
    assert "=== globus ===" in result.output


def test_command_parsing(run_line):
    """
    Runs list-commands --help
    confirms both the command and the option are parsed
    """
    result = run_line("globus list-commands --help")
    assert "List all Globus CLI Commands with short help output." in result.output


def test_invalid_command(run_line):
    result = run_line("globus invalid-command", assert_exit_code=2)
    assert "Error: No such command" in result.stderr


def test_json_raw_string_output(run_line, userinfo_mocker):
    """
    Get single-field jmespath output and make sure it's quoted.
    """
    userinfo_mocker.configure_unlinked(name="Geordi La Forge")
    result = run_line("globus whoami --jmespath name")
    assert '"Geordi La Forge"\n' == result.output


def test_transfer_call(run_line):
    """
    Runs ls using test transfer refresh token to confirm
    test transfer refresh token is live and configured correctly
    """
    epid = str(uuid.UUID(int=1))
    load_response(
        RegisteredResponse(
            service="transfer",
            path=f"/v0.10/operation/endpoint/{epid}/ls",
            json={
                # not *quite* verbatim data from the API, but very similar and in the
                # right format with all fields populated
                "DATA": [
                    {
                        "DATA_TYPE": "file",
                        "group": "root",
                        "last_modified": "2021-01-14 00:33:38+00:00",
                        "link_group": None,
                        "link_last_modified": None,
                        "link_size": None,
                        "link_target": None,
                        "link_user": None,
                        "name": name,
                        "permissions": "0755",
                        "size": 4096,
                        "type": "dir",
                        "user": "root",
                    }
                    for name in ["home", "mnt", "not shareable", "share"]
                ]
            },
        )
    )
    result = run_line("globus ls " + epid + ":/")
    assert "home/" in result.output


@pytest.mark.parametrize("output_format", ["json", "text"])
def test_transfer_batch_stdin_dryrun(run_line, go_ep1_id, go_ep2_id, output_format):
    """
    Dry-runs a transfer in batchmode, confirms batchmode inputs received.
    """
    # put a submission ID response in place
    load_response_set("cli.get_submission_id")

    batch_input = "abc /def\n/xyz p/q/r\n"
    result = run_line(
        f"globus transfer -F {output_format} --batch - "
        f"--dry-run {go_ep1_id} {go_ep2_id}",
        stdin=batch_input,
    )
    for src, dst in [("abc", "/def"), ("/xyz", "p/q/r")]:
        if output_format == "json":
            assert f'"source_path": "{src}"' in result.output
            assert f'"destination_path": "{dst}"' in result.output
        else:
            src_dst_columns_regex = re.compile(
                re.escape(src) + r"\s+|\s+" + re.escape(dst)
            )
            assert src_dst_columns_regex.search(result.output) is not None


def test_transfer_batch_file_dryrun(run_line, go_ep1_id, go_ep2_id, tmp_path):
    # put a submission ID response in place
    load_response_set("cli.get_submission_id")
    temp = tmp_path / "batch"
    temp.write_text("abc /def\n/xyz p/q/r\n")
    result = run_line(
        [
            "globus",
            "transfer",
            "-F",
            "json",
            "--batch",
            temp,
            "--dry-run",
            go_ep1_id,
            go_ep2_id,
        ]
    )
    for src, dst in [("abc", "/def"), ("/xyz", "p/q/r")]:
        assert f'"source_path": "{src}"' in result.output
        assert f'"destination_path": "{dst}"' in result.output


def test_delete_batchmode_dryrun(run_line, go_ep1_id):
    """
    Dry-runs a delete in batchmode.
    """
    # put a submission ID response in place
    load_response_set("cli.get_submission_id")

    batch_input = "abc/def\n/xyz\nabcdef\nabc/def/../xyz\n"
    result = run_line(
        "globus delete --batch - --dry-run " + go_ep1_id, stdin=batch_input
    )
    assert (
        "\n".join(
            ("Path   ", "-------", "abc/def", "/xyz   ", "abcdef ", "abc/xyz", "")
        )
        == result.output
    )

    batch_input = "abc/def\n/xyz\n../foo\n"
    result = run_line(
        f"globus delete --batch - --dry-run {go_ep1_id}:foo/bar/./baz",
        stdin=batch_input,
    )
    assert (
        "\n".join(
            (
                "Path               ",
                "-------------------",
                "foo/bar/baz/abc/def",
                "/xyz               ",
                "foo/bar/foo        ",
                "",
            )
        )
        == result.output
    )


@pytest.mark.parametrize("cmd", ["list-commands", "version", "whoami"])
def test_env_checks(monkeypatch, run_line, cmd):
    """
    Test that passing garbage values for specific environment variables causes an error
    with a specific message. (This test just parametrizes over a few example commands
    that don't require extra input to run.)
    """
    monkeypatch.setitem(os.environ, "GLOBUS_CLI_INTERACTIVE", "Whoops")
    result = run_line(f"globus {cmd}", assert_exit_code=1)
    assert "GLOBUS_CLI_INTERACTIVE" in result.stderr


@pytest.mark.parametrize("option", ("--recursive", "--no-recursive"))
def test_recursive_and_batch_exclusive(run_line, option):
    ep_id = str(uuid.UUID(int=1))

    result = run_line(
        [
            "globus",
            "transfer",
            ep_id,
            ep_id,
            option,
            "--batch",
            "-",
        ],
        assert_exit_code=2,
    )
    assert f"You cannot use `{option}` in addition to `--batch`" in result.stderr


@pytest.mark.parametrize(
    "deletion_option,recursion_option,expected_error",
    (
        ("--delete-destination-extra", "--recursive", ""),
        ("--delete-destination-extra", "", ""),
        (
            "--delete-destination-extra",
            "--no-recursive",
            (
                "The `--delete-destination-extra` option cannot be specified with "
                "`--no-recursive`."
            ),
        ),
        ("--delete", "--recursive", ""),
        ("--delete", "", ""),
        (
            "--delete",
            "--no-recursive",
            "The `--delete` option cannot be specified with `--no-recursive`.",
        ),
    ),
)
def test_no_recursive_and_delete_exclusive(
    run_line,
    deletion_option,
    recursion_option,
    expected_error,
):
    load_response("transfer.get_submission_id")
    load_response("transfer.submit_transfer")
    ep_meta = load_response("transfer.get_endpoint").metadata
    ep_id = ep_meta["endpoint_id"]

    base_cmd = f"globus transfer {ep_id}:/foo/ {ep_id}:/bar/"
    options = f"{deletion_option} {recursion_option}"

    exit_code = 0 if not expected_error else 2
    result = run_line(f"{base_cmd} {options}", assert_exit_code=exit_code)

    assert expected_error in result.stderr


def test_legacy_delete_and_delete_destination_are_mutex(run_line):
    ep_id = str(uuid.UUID(int=1))
    result = run_line(
        [
            "globus",
            "transfer",
            "--delete",
            "--delete-destination-extra",
            ep_id,
            ep_id,
        ],
        assert_exit_code=2,
    )
    assert "mutually exclusive" in result.stderr


def test_legacy_delete_flag_deprecation_warning(run_line):
    ep_id = str(uuid.UUID(int=1))
    result = run_line(
        [
            "globus",
            "transfer",
            "--delete",
            ep_id,
            ep_id,
        ],
        assert_exit_code=2,
    )
    assert "`--delete` has been deprecated" in result.stderr
