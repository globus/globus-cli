import json

import pytest
import responses
from globus_sdk._testing import load_response_set


@pytest.mark.parametrize("datatype_field", [None, "GIngest"])
def test_gingest_document(run_line, tmp_path, datatype_field):
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]

    data = {
        "ingest_type": "GMetaEntry",
        "ingest_data": {
            "@datatype": "GMetaEntry",
            "content": {"alpha": {"beta": "delta"}},
            "id": "testentry2",
            "subject": "http://example.com",
            "visible_to": ["public"],
        },
    }
    if datatype_field is not None:
        data["@datatype"] = "GIngest"

    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(data))

    result, matcher = run_line(
        ["globus", "search", "ingest", index_id, str(doc)], matcher=True
    )
    matcher.check(r"^Acknowledged:\s+(\w+)$", groups=["True"])
    matcher.check(r"^Task ID:\s+([\w-]+)$")

    sent = responses.calls[-1].request
    assert sent.method == "POST"
    sent_body = json.loads(sent.body)
    assert sent_body["ingest_data"] == data["ingest_data"]


@pytest.mark.parametrize("datatype", ["GMetaEntry", "GMetaList"])
def test_auto_wrap_document(run_line, tmp_path, datatype):
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]

    entry_data = {
        "@datatype": "GMetaEntry",
        "content": {"alpha": {"beta": "delta"}},
        "id": "testentry2",
        "subject": "http://example.com",
        "visible_to": ["public"],
    }
    if datatype == "GMetaEntry":
        data = entry_data
    elif datatype == "GMetaList":
        data = {"@datatype": "GMetaList", "gmeta": [entry_data]}
    else:
        raise NotImplementedError

    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(data))

    result, matcher = run_line(
        ["globus", "search", "ingest", index_id, str(doc)], matcher=True
    )
    matcher.check(r"^Acknowledged:\s+(\w+)$", groups=["True"])
    matcher.check(r"^Task ID:\s+([\w-]+)$")

    sent = responses.calls[-1].request
    assert sent.method == "POST"
    sent_body = json.loads(sent.body)
    assert sent_body["@datatype"] == "GIngest"
    assert sent_body["ingest_type"] == datatype
    assert sent_body["ingest_data"] == data


def test_auto_wrap_document_rejects_bad_doctype(run_line, tmp_path):
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]

    data = {"@datatype": "NoSuchDocumentType"}

    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(data))

    result = run_line(
        ["globus", "search", "ingest", index_id, str(doc)], assert_exit_code=2
    )
    assert "Unsupported datatype: 'NoSuchDocumentType'" in result.stderr


def test_ingest_rejects_non_object_data(run_line, tmp_path):
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]

    data = ["foo", "bar"]
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(data))

    result = run_line(
        ["globus", "search", "ingest", index_id, str(doc)], assert_exit_code=2
    )
    assert "Ingest document must be a JSON object" in result.stderr
