import unittest.mock

import click
import pytest

from globus_cli.utils import (
    format_list_of_words,
    format_plural_str,
    shlex_process_stream,
    unquote_cmdprompt_single_quotes,
)


def test_format_word_list():
    assert format_list_of_words("alpha") == "alpha"
    assert format_list_of_words("alpha", "beta") == "alpha and beta"
    assert format_list_of_words("alpha", "beta", "gamma") == "alpha, beta, and gamma"
    assert (
        format_list_of_words("alpha", "beta", "gamma", "delta")
        == "alpha, beta, gamma, and delta"
    )


def test_format_plural_str():
    fmt = "you need to run {this} {command}"
    wordforms = {"this": "these", "command": "commands"}
    assert format_plural_str(fmt, wordforms, True) == "you need to run these commands"
    assert format_plural_str(fmt, wordforms, False) == "you need to run this command"


@pytest.mark.parametrize(
    "arg, expect",
    (
        ("foo", "foo"),
        ("'foo'", "foo"),
        ("'", "'"),
        ("'foo", "'foo"),
        ("foo'", "foo'"),
        ("''", ""),
        ('"foo"', '"foo"'),
    ),
)
def test_unquote_cmdprompt_squote(arg, expect):
    assert unquote_cmdprompt_single_quotes(arg) == expect


def test_shlex_process_stream_success():
    @click.command()
    def outer_main():
        pass

    values = []

    @click.command()
    @click.argument("bar")
    def foo(bar):
        values.append(bar)

    text_like = unittest.mock.Mock()
    text_like.readlines.return_value = ["alpha\n", "beta  # gamma\n"]
    text_like.name = "alphabet.txt"

    with outer_main.make_context("main", []):
        shlex_process_stream(foo, text_like, "data")
    assert values == ["alpha", "beta"]


def test_shlex_process_stream_error_handling(capsys):
    @click.command()
    def outer_main():
        pass

    values = []

    @click.command()
    @click.argument("bar")
    def foo(bar):
        values.append(bar)

    text_like = unittest.mock.Mock()
    text_like.readlines.return_value = ["alpha beta\n"]
    text_like.name = "alphabet.txt"

    with pytest.raises(click.exceptions.Exit) as excinfo:
        with outer_main.make_context("main", []):
            shlex_process_stream(foo, text_like, "data")

    assert excinfo.value.exit_code == 2
    captured = capsys.readouterr()
    assert (
        """\
error encountered processing 'data' at alphabet.txt:0:
  Got unexpected extra argument (beta)
"""
        in captured.err
    )
