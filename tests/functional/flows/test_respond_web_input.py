from __future__ import annotations

import functools
import json
import pathlib
import typing as t

from globus_sdk.testing import get_last_request, load_response


@functools.cache
def _respond_file_path(test_file_dir: str) -> tuple[pathlib.Path, t.Any]:
    path = pathlib.Path(test_file_dir) / "flows/respond-to-web-input-file.json"
    content = json.loads(path.read_text())
    return path, content


def test_respond_web_input_with_option_id(run_line):
    loaded_response = load_response("flows.respond_to_web_input")
    meta = loaded_response.metadata
    web_input_id = meta["web_input_id"]
    option_id = meta["option_id"]

    result = run_line(
        ["globus", "flows", "web-input", "respond", web_input_id, option_id]
    )
    assert "Status:" in result.output
    assert "ok" in result.output

    req = get_last_request()
    sent_body = json.loads(req.body)
    assert sent_body == {"response": {"value": option_id}}


def test_respond_web_input_with_file(run_line, test_file_dir):
    loaded_response = load_response("flows.respond_to_web_input")
    web_input_id = loaded_response.metadata["web_input_id"]
    path, content = _respond_file_path(test_file_dir)

    result = run_line(
        [
            "globus",
            "flows",
            "web-input",
            "respond",
            web_input_id,
            "--file",
            str(path),
        ]
    )
    assert "Status:" in result.output
    assert "ok" in result.output

    req = get_last_request()
    sent_body = json.loads(req.body)
    assert sent_body == {"response": {"value": content}}


def test_respond_web_input_option_id_and_file_are_mutually_exclusive(
    run_line, test_file_dir
):
    loaded_response = load_response("flows.respond_to_web_input")
    meta = loaded_response.metadata
    path, _ = _respond_file_path(test_file_dir)
    web_input_id = meta["web_input_id"]
    option_id = meta["option_id"]

    result = run_line(
        [
            "globus",
            "flows",
            "web-input",
            "respond",
            web_input_id,
            option_id,
            "--file",
            str(path),
        ],
        assert_exit_code=2,
    )
    assert "OPTION_ID and --file are mutually exclusive" in result.stderr


def test_respond_web_input_requires_option_id_or_file(run_line):
    loaded_response = load_response("flows.respond_to_web_input")
    web_input_id = loaded_response.metadata["web_input_id"]

    result = run_line(
        ["globus", "flows", "web-input", "respond", web_input_id],
        assert_exit_code=2,
    )
    assert "Either OPTION_ID or '--file' must be provided." in result.stderr
