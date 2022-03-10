import json
import uuid

import pytest
import responses
from globus_sdk._testing import load_response, register_response_set


@pytest.fixture(autouse=True, scope="session")
def _register_dbq_responses():
    index_id = str(uuid.uuid1())
    task_id = str(uuid.uuid1())
    common_meta = {"index_id": index_id, "task_id": task_id}
    register_response_set(
        "delete_by_query",
        {
            "default": {
                "service": "search",
                "path": f"/v1/index/{index_id}/delete_by_query",
                "method": "POST",
                "json": {
                    "task_id": task_id,
                },
                "metadata": common_meta,
            }
        },
        metadata=common_meta,
    )


@pytest.mark.parametrize("advanced_mode", [True, False])
def test_dbq_query_string(run_line, advanced_mode):
    """
    Runs 'globus search query -q ...' and validates results
    """
    meta = load_response("delete_by_query").metadata
    index_id = meta["index_id"]
    task_id = meta["task_id"]

    add_args = []
    if advanced_mode:
        add_args = ["--advanced"]
    result = run_line(
        ["globus", "search", "delete-by-query", index_id, "-q", "tomatillo"] + add_args
    )

    assert task_id in result.output

    sent = responses.calls[-1].request
    assert sent.method == "POST"
    sent_body = json.loads(sent.body)
    assert sent_body["q"] == "tomatillo"
    if advanced_mode:
        assert sent_body["advanced"] is True
    else:
        assert "advanced" not in sent_body


def test_dbq_query_document(run_line, tmp_path):
    """
    Runs 'globus search query --query-document ...' and validates results
    """
    meta = load_response("delete_by_query").metadata
    index_id = meta["index_id"]
    task_id = meta["task_id"]
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps({"q": "tomatillo"}))

    result = run_line(
        ["globus", "search", "delete-by-query", index_id, "--query-document", str(doc)]
    )

    assert task_id in result.output

    sent = responses.calls[-1].request
    assert sent.method == "POST"
    sent_body = json.loads(sent.body)
    assert sent_body["q"] == "tomatillo"


def test_dbq_query_string_and_document_mutex(run_line, tmp_path):
    """
    Check that `-q` and `--query-document` cannot be used together
    """
    meta = load_response("delete_by_query").metadata
    index_id = meta["index_id"]
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps({"q": "tomatillo"}))

    result = run_line(
        [
            "globus",
            "search",
            "delete-by-query",
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
    meta = load_response("delete_by_query").metadata
    index_id = meta["index_id"]

    result = run_line(
        [
            "globus",
            "search",
            "delete-by-query",
            index_id,
        ],
        assert_exit_code=2,
    )
    assert "Either '-q' or '--query-document' must be provided" in result.stderr
