import os
import re

import click
import pytest

from globus_cli.termio import Field, TextMode, display, formatters, term_is_interactive


@pytest.mark.parametrize(
    "ps1, force_flag, expect",
    [
        (None, None, False),
        (None, "TRUE", True),
        (None, "0", False),
        ("$ ", None, True),
        ("$ ", "off", False),
        ("$ ", "on", True),
        ("$ ", "", True),
        ("", "", True),
        ("", None, True),
    ],
)
def test_term_interactive(ps1, force_flag, expect, monkeypatch):
    if ps1 is not None:
        monkeypatch.setitem(os.environ, "PS1", ps1)
    else:
        monkeypatch.delitem(os.environ, "PS1", raising=False)
    if force_flag is not None:
        monkeypatch.setitem(os.environ, "GLOBUS_CLI_INTERACTIVE", force_flag)
    else:
        monkeypatch.delitem(os.environ, "GLOBUS_CLI_INTERACTIVE", raising=False)

    assert term_is_interactive() == expect


def test_format_record_list(capsys):
    data = [
        {"bird": "Killdeer", "wingspan": 46},
        {"bird": "Franklin's Gull", "wingspan": 91},
    ]
    fields = [Field("Bird", "bird"), Field("Wingspan", "wingspan")]
    with click.Context(click.Command("fake-command")) as _:
        display(data, text_mode=TextMode.text_record_list, fields=fields)
    output = capsys.readouterr().out
    # Should have:
    # 5 lines in total,
    assert len(output.splitlines()) == 5
    # and one empty line between the records
    assert "" in output.splitlines()
    assert re.match(r"Bird:\s+Killdeer", output)


def test_dot_nested_field_lookup():
    nested_field = Field("foobarbaz", "foo.bar.baz")
    assert nested_field.get_value({"foo": {}}) is None
    assert nested_field.get_value({"foo": {"bar": {}}}) is None
    assert nested_field.get_value({"foo": {"bar": {"baz": None}}}) is None
    assert nested_field.get_value({"foo": {"bar": {"baz": "buzz"}}}) == "buzz"


def test_date_format():
    f = Field("foo", "foo", formatter=formatters.Date)
    assert f({"foo": None}) == "None"
    assert f({"foo": "2022-04-05T16:27:48.805427"}) == "2022-04-05 16:27:48"


def test_bool_format():
    f = Field("foo", "foo", formatter=formatters.Bool)
    assert f({"foo": None}) == "None"
    assert f({}) == "None"
    assert f({"foo": True}) == "True"
    assert f({"foo": False}) == "False"

    with pytest.warns(formatters.FormattingFailedWarning):
        assert f({"foo": "hi there"}) == "hi there"


def test_fuzzy_bool_format():
    f = Field("foo", "foo", formatter=formatters.FuzzyBool)
    assert f({"foo": None}) == "False"
    assert f({}) == "False"
    assert f({"foo": True}) == "True"
    assert f({"foo": False}) == "False"
    assert f({"foo": "hi there"}) == "True"
