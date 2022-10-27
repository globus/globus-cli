import pytest

from globus_cli.termio import Field, formatters


def test_date_format_badly_typed_input():
    fmt = formatters.DateFormatter()
    with pytest.warns(formatters.FormattingFailedWarning):
        data = fmt.format(0)
    assert data == "0"


def test_date_format_via_field():
    f = Field("foo", "foo", formatter=formatters.Date)
    assert f({"foo": None}) == "None"
    assert f({"foo": "2022-04-05T16:27:48.805427"}) == "2022-04-05 16:27:48"


def test_bool_format_via_field():
    f = Field("foo", "foo", formatter=formatters.Bool)
    assert f({"foo": None}) == "None"
    assert f({}) == "None"
    assert f({"foo": True}) == "True"
    assert f({"foo": False}) == "False"

    with pytest.warns(formatters.FormattingFailedWarning):
        assert f({"foo": "hi there"}) == "hi there"


def test_fuzzy_bool_format_via_field():
    f = Field("foo", "foo", formatter=formatters.FuzzyBool)
    assert f({"foo": None}) == "False"
    assert f({}) == "False"
    assert f({"foo": True}) == "True"
    assert f({"foo": False}) == "False"
    assert f({"foo": "hi there"}) == "True"
