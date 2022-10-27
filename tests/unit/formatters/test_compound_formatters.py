import json

import pytest

from globus_cli.termio import formatters


@pytest.mark.parametrize(
    "data",
    [None, True, False, {"foo": "bar"}, 1.0, 1, ["foo", {"bar": "baz"}], "foo-bar"],
)
def test_format_valid_json_value(data):
    fmt = formatters.SortedJsonFormatter()
    result = fmt.format(data)
    assert result == json.dumps(data, sort_keys=True)


def test_formatting_invalid_json_value():
    # `json.dumps` supports tuples, but the SortedJsonFormatter does not
    data = (1, 2)
    fmt = formatters.SortedJsonFormatter()
    with pytest.warns(formatters.FormattingFailedWarning):
        result = fmt.format(data)
    assert result == str(data)
