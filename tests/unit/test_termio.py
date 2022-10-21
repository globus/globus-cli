import os
import re

import click
import pytest

from globus_cli.termio import (
    FORMAT_TEXT_RECORD_LIST,
    Field,
    formatted_print,
    term_is_interactive,
)


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
        formatted_print(data, text_format=FORMAT_TEXT_RECORD_LIST, fields=fields)
    output = capsys.readouterr().out
    # Should have:
    # 5 lines in total,
    assert len(output.splitlines()) == 5
    # and one empty line between the records
    assert "" in output.splitlines()
    assert re.match(r"Bird:\s+Killdeer", output)
