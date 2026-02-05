import os
import re
import textwrap
from unittest import mock

import click
import pytest

from globus_cli.termio import Field, display, term_is_interactive


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
        display(data, text_mode=display.RECORD_LIST, fields=fields)
    output = capsys.readouterr().out
    # Should have:
    # 5 lines in total,
    assert len(output.splitlines()) == 5
    # and one empty line between the records
    assert "" in output.splitlines()
    assert re.match(r"Bird:\s+Killdeer", output)


def test_format_record_with_text_wrapping(capsys, monkeypatch):
    # fake the terminal width at 120
    fake_dimensions = mock.Mock()
    fake_dimensions.columns = 120
    monkeypatch.setattr("shutil.get_terminal_size", lambda *_, **__: fake_dimensions)
    expected_width = int(0.8 * 120)

    # based on info from wikipedia
    data = {
        "bird": "Franklin's Gull",
        "description": textwrap.dedent("""
            A migratory gull with a range spanning from Chile and
            Argentina up to Canada and Alaska.
            Named after the Arctic explorer Sir John Franklin, it
            has a white body, dark grey wings, and a black hood.
            The black hood plumage, developed in the breeding season,
            is lost in the winter.
            """).replace("\n", " ").strip(),
    }
    fields = [
        Field("Bird", "bird"),
        Field("Description", "description", wrap_enabled=True),
    ]

    with click.Context(click.Command("fake-command")) as _:
        display(data, text_mode=display.RECORD, fields=fields)
    output_lines = capsys.readouterr().out.splitlines()

    # output should be more than two lines
    assert len(output_lines) > 2
    # the first line is the name field
    assert re.match(r"^Bird:\s+Franklin's Gull$", output_lines[0])
    # second line starts with the description field name,
    # but is limited in width for the value
    # give it a lower bound to show that it's not tightly wrapped (most of the words
    # in the description text are < 10 chars)
    assert re.match(r"^Description:\s+.*$", output_lines[1])
    assert (expected_width - 10) < len(output_lines[1]) <= expected_width

    # check the rest of the output against a manual wrap of the description text
    # exactly in the way in which it is expected to be wrapped (but without the indent)
    wrapped_description_lines = textwrap.fill(
        data["description"], width=expected_width - len("Description: ")
    ).splitlines()

    for i, line in enumerate(wrapped_description_lines[1:]):
        assert output_lines[i + 2].endswith(line)
