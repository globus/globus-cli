import pytest

from globus_cli.utils import (
    format_list_of_words,
    format_plural_str,
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
