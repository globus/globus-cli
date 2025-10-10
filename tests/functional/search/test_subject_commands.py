import json

import pytest
import responses
from globus_sdk.testing import load_response_set


@pytest.mark.parametrize("multiple_entries", (False, True))
def test_search_subject_show(run_line, multiple_entries):
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]
    subject = meta["multi_entry_subject"] if multiple_entries else meta["subject"]

    res = run_line(["globus", "search", "subject", "show", index_id, subject])
    data = json.loads(res.output)
    if multiple_entries:
        assert isinstance(data, list)
        for item in data:
            assert "entry_id" in item
            assert "content" in item
    else:
        assert isinstance(data, dict)
        assert "content" in data
        assert "entry_id" in data

    sent = responses.calls[-1].request
    assert sent.method == "GET"
    assert sent.params == {"subject": subject}
    assert sent.body is None


def test_search_subject_delete(run_line):
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]
    subject = meta["subject"]

    res = run_line(["globus", "search", "subject", "delete", index_id, subject])
    assert meta["delete_by_subject_task_id"] in res.output

    sent = responses.calls[-1].request
    assert sent.method == "DELETE"
    assert sent.params == {"subject": subject}
    assert sent.body is None
