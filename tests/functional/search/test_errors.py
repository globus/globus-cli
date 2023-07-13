import json

from globus_sdk._testing import load_response_set


def test_notfound_error(run_line):
    meta = load_response_set("cli.search").metadata
    index_id = meta["error_index_id"]

    run_line(
        ["globus", "search", "query", index_id, "-q", "*"],
        assert_exit_code=1,
        search_stderr=[
            ("code", "NotFound.NoSuchIndex"),
            f'There is no search index named "{index_id}"',
        ],
    )


def test_validation_error(run_line, tmp_path):
    meta = load_response_set("cli.search").metadata
    index_id = meta["error_index_id"]

    # although not strictly necessary for the test (since we mock the response data),
    # this is an example of the malformed data on submit: missing 'visible_to', which
    # is a required field
    data = {
        "ingest_type": "GMetaEntry",
        "ingest_data": {
            "@datatype": "GMetaEntry",
            "content": {"alpha": {"beta": "delta"}},
            "id": "testentry2",
            "subject": "http://example.com",
        },
    }

    doc = tmp_path / "doc.json"
    doc.write_text(json.dumps(data))

    run_line(
        ["globus", "search", "ingest", index_id, str(doc)],
        assert_exit_code=1,
        search_stderr=[
            ("code", "BadRequest.ValidationError"),
            "Missing data for required field.",
        ],
    )
