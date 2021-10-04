import json

import pytest
import responses


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
def test_query_string(run_line, load_api_fixtures, addargs, expect_params):
    """
    Runs 'globus search query -q ...' and validates results
    """
    data = load_api_fixtures("search.yaml")
    index_id = data["metadata"]["index_id"]

    result = run_line(
        ["globus", "search", "query", index_id, "-q", "tomatillo"] + addargs
    )

    assert "simmer 20 minutes" in result.output
    data = json.loads(result.output)
    assert data["count"] == 1
    assert [x["subject"] for x in data["gmeta"]] == [
        "https://en.wikipedia.org/wiki/Salsa_verde"
    ]

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
def test_query_document(run_line, load_api_fixtures, tmp_path, addargs, expect_params):
    """
    Runs 'globus search query --query-document ...' and validates results
    """
    data = load_api_fixtures("search.yaml")
    index_id = data["metadata"]["index_id"]
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps({"q": "tomatillo"}))

    result = run_line(
        ["globus", "search", "query", index_id, "--query-document", str(doc)] + addargs
    )

    assert "simmer 20 minutes" in result.output
    data = json.loads(result.output)
    assert data["count"] == 1
    assert [x["subject"] for x in data["gmeta"]] == [
        "https://en.wikipedia.org/wiki/Salsa_verde"
    ]

    sent = responses.calls[-1].request
    assert sent.method == "POST"
    assert "q" not in sent.params
    sent_body = json.loads(sent.body)
    assert "q" in sent_body
    assert sent_body["q"] == "tomatillo"
    for k, v in expect_params.items():
        assert k in sent_body
        assert sent_body[k] == v


def test_query_string_and_document_mutex(run_line, load_api_fixtures, tmp_path):
    """
    Check that `-q` and `--query-document` cannot be used together
    """
    data = load_api_fixtures("search.yaml")
    index_id = data["metadata"]["index_id"]
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


def test_query_required(run_line, load_api_fixtures):
    """
    Check that at least one of `-q` or `--query-document` must be provided
    """
    data = load_api_fixtures("search.yaml")
    index_id = data["metadata"]["index_id"]

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
