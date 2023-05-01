import json

import pytest
import responses
from globus_sdk._testing import load_response_set


@pytest.mark.parametrize(
    "addargs, expect_params",
    [
        ([], {}),
        (["--limit", 10], {"limit": "10"}),
        (["--advanced", "--limit", 10], {"limit": "10", "advanced": "True"}),
        (["--bypass-visible-to"], {"bypass_visible_to": "True"}),
        (
            ["--filter-principal-sets", "admin,manager"],
            {"filter_principal_sets": "admin,manager"},
        ),
    ],
)
def test_query_string(run_line, addargs, expect_params):
    """
    Runs 'globus search query -q ...' and validates results
    """
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]

    result = run_line(
        ["globus", "search", "query", index_id, "-q", "tomatillo"] + addargs
    )

    assert result.output.strip() == "https://en.wikipedia.org/wiki/Salsa_verde"

    sent = responses.calls[-1].request
    assert sent.method == "GET"
    assert sent.params["q"] == "tomatillo"
    for k, v in expect_params.items():
        assert k in sent.params
        assert sent.params[k] == v


@pytest.mark.parametrize(
    "addargs, expect_params",
    [
        ([], {}),
        (["--limit", 10], {"limit": 10}),
        (["--advanced", "--limit", 10], {"limit": 10, "advanced": True}),
        (["--bypass-visible-to"], {"bypass_visible_to": True}),
        (
            ["--filter-principal-sets", "admin,manager"],
            {"filter_principal_sets": ["admin", "manager"]},
        ),
    ],
)
def test_query_document(run_line, tmp_path, addargs, expect_params):
    """
    Runs 'globus search query --query-document ...' and validates results
    """
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps({"q": "tomatillo"}))

    result = run_line(
        ["globus", "search", "query", index_id, "--query-document", str(doc)] + addargs
    )

    assert result.output.strip() == "https://en.wikipedia.org/wiki/Salsa_verde"

    sent = responses.calls[-1].request
    assert sent.method == "POST"
    assert "q" not in sent.params
    sent_body = json.loads(sent.body)
    assert "q" in sent_body
    assert sent_body["q"] == "tomatillo"
    for k, v in expect_params.items():
        assert k in sent_body
        assert sent_body[k] == v


def test_query_string_and_document_mutex(run_line, tmp_path):
    """
    Check that `-q` and `--query-document` cannot be used together
    """
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps({"q": "tomatillo"}))

    result = run_line(
        [
            "globus",
            "search",
            "query",
            index_id,
            "-q",
            "tomatillo",
            "--query-document",
            str(doc),
        ],
        assert_exit_code=2,
    )
    assert "mutually exclusive" in result.stderr


def test_query_required(run_line):
    """
    Check that at least one of `-q` or `--query-document` must be provided
    """
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]

    result = run_line(
        [
            "globus",
            "search",
            "query",
            index_id,
        ],
        assert_exit_code=2,
    )
    assert "Either '-q' or '--query-document' must be provided" in result.stderr


def test_query_rejects_non_object_document(run_line, tmp_path):
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(["foo", "bar"]))

    result = run_line(
        [
            "globus",
            "search",
            "query",
            index_id,
            "--query-document",
            str(doc),
        ],
        assert_exit_code=2,
    )
    assert "--query-document must be a JSON object" in result.stderr
