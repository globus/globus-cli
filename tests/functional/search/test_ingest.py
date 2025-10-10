import json
import uuid

import pytest
import responses
from globus_sdk.testing import RegisteredResponse, load_response


@pytest.fixture
def search_ingest_response():
    task_id = str(uuid.uuid1())
    index_id = str(uuid.uuid1())
    return load_response(
        RegisteredResponse(
            service="search",
            path=f"/v1/index/{index_id}/ingest",
            method="POST",
            json={
                "acknowledged": True,
                "task_id": task_id,
            },
            metadata={
                "index_id": index_id,
                "task_id": task_id,
            },
        )
    )


@pytest.mark.parametrize("datatype_field", [None, "GIngest"])
def test_gingest_document(run_line, tmp_path, datatype_field, search_ingest_response):
    index_id = search_ingest_response.metadata["index_id"]
    task_id = search_ingest_response.metadata["task_id"]

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

    run_line(
        ["globus", "search", "ingest", index_id, str(doc)],
        search_stdout=[
            ("Acknowledged", "True"),
            ("Task ID", task_id),
        ],
    )

    sent = responses.calls[-1].request
    assert sent.method == "POST"
    sent_body = json.loads(sent.body)
    assert sent_body["ingest_data"] == data["ingest_data"]


@pytest.mark.parametrize("datatype", ["GMetaEntry", "GMetaList"])
def test_auto_wrap_document(run_line, tmp_path, datatype, search_ingest_response):
    index_id = search_ingest_response.metadata["index_id"]
    task_id = search_ingest_response.metadata["task_id"]

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

    run_line(
        ["globus", "search", "ingest", index_id, str(doc)],
        search_stdout=[
            ("Acknowledged", "True"),
            ("Task ID", task_id),
        ],
    )

    sent = responses.calls[-1].request
    assert sent.method == "POST"
    sent_body = json.loads(sent.body)
    assert sent_body["@datatype"] == "GIngest"
    assert sent_body["ingest_type"] == datatype
    assert sent_body["ingest_data"] == data


def test_auto_wrap_document_rejects_bad_doctype(
    run_line, tmp_path, search_ingest_response
):
    index_id = search_ingest_response.metadata["index_id"]

    data = {"@datatype": "NoSuchDocumentType"}

    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(data))

    run_line(
        ["globus", "search", "ingest", index_id, str(doc)],
        assert_exit_code=2,
        search_stderr="Unsupported datatype: 'NoSuchDocumentType'",
    )


def test_ingest_rejects_non_object_data(run_line, tmp_path, search_ingest_response):
    index_id = search_ingest_response.metadata["index_id"]

    data = ["foo", "bar"]
    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(data))

    run_line(
        ["globus", "search", "ingest", index_id, str(doc)],
        assert_exit_code=2,
        search_stderr="Ingest document must be a JSON object",
    )
