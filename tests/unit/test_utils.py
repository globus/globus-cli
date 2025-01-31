import unittest.mock

import click
import pytest

from globus_cli.services.auth import CustomAuthClient
from globus_cli.utils import (
    LazyDict,
    format_list_of_words,
    format_plural_str,
    resolve_principal_urn,
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
error encountered processing 'data' in alphabet.txt at line 0:
  Got unexpected extra argument (beta)
"""
        in captured.err
    )


@pytest.mark.parametrize(
    "principal, resolve_id, expect_error",
    (
        # -- Success Cases --
        # Username which resolves to a UUID
        ("foo@globus.org", True, False),
        # Identity URN
        ("urn:globus:auth:identity:64831427-e501-420b-93da-9e4efee3dd51", False, False),
        # Group URN
        ("urn:globus:groups:id:449718d5-32b2-48ba-bd46-e045deab5430", False, False),
        # Plain UUID (Assume it's an identity)
        ("64831427-e501-420b-93da-9e4efee3dd51", True, False),
        # -- Error Cases --
        # Username which doesn't resolve to a UUID
        ("bar@globus.org", False, True),
    ),
)
def test_resolve_principal_urn__when_principal_type_is_omitted(
    principal, resolve_id, expect_error
):
    """
    Verifies success & error cases for principal resolution when principal_type is
      omitted (i.e. None).
    """
    # === Setup ===
    auth_client = unittest.mock.Mock(spec=CustomAuthClient)
    resolved_id = "64831427-e501-420b-93da-9e4efee3dd51" if resolve_id else None
    auth_client.maybe_lookup_identity_id.return_value = resolved_id

    try:
        # === Act ===
        urn = resolve_principal_urn(
            auth_client=auth_client,
            principal=principal,
            principal_type=None,
        )
    except click.UsageError as e:
        # === Verify (Failure Case) ===
        assert expect_error
        assert e.message == (
            f"'--principal-type' was unspecified and '{principal}' was not resolvable "
            f"to a globus identity."
        )
    else:
        # === Verify (Success Case) ===
        assert not expect_error
        assert (
            urn == "urn:globus:auth:identity:64831427-e501-420b-93da-9e4efee3dd51"
            or urn == "urn:globus:groups:id:449718d5-32b2-48ba-bd46-e045deab5430"
        )


@pytest.mark.parametrize(
    "principal, resolve_id, expect_error",
    (
        # -- Success Cases --
        # Username which resolves to a UUID
        ("foo@globus.org", True, False),
        # UUID (resolves to itself)
        ("64831427-e501-420b-93da-9e4efee3dd51", True, False),
        # Identity URN (no resolution needed)
        ("urn:globus:auth:identity:64831427-e501-420b-93da-9e4efee3dd51", False, False),
        # -- Error Cases --
        # Username which doesn't resolve to a UUID
        ("bar@globus.org", False, True),
        # Non-identity URN (we let it resolve to a UUID if attempted, but it shouldn't)
        ("urn:globus:groups:id:449718d5-32b2-48ba-bd46-e045deab5430", True, True),
    ),
)
def test_resolve_principal_urn__when_principal_type_is_identity(
    principal, resolve_id, expect_error
):
    """
    Verifies success & error cases for principal resolution when principal_type is
      explicitly set to "identity".
    """
    # === Setup ===
    auth_client = unittest.mock.Mock(spec=CustomAuthClient)
    resolved_id = "64831427-e501-420b-93da-9e4efee3dd51" if resolve_id else None
    auth_client.maybe_lookup_identity_id.return_value = resolved_id

    try:
        # === Act ===
        urn = resolve_principal_urn(
            auth_client=auth_client,
            principal=principal,
            principal_type="identity",
        )
    except click.UsageError as e:
        # === Verify (Error Case) ===
        assert expect_error
        assert e.message == (
            f"'--principal-type identity' but '{principal}' is not a valid username, "
            "identity UUID, or identity URN"
        )
    else:
        # === Verify (Success Case) ===
        assert not expect_error
        assert urn == "urn:globus:auth:identity:64831427-e501-420b-93da-9e4efee3dd51"


@pytest.mark.parametrize(
    "principal, expect_error",
    (
        # -- Success Cases --
        # Group UUID
        ("449718d5-32b2-48ba-bd46-e045deab5430", False),
        # Group URN
        ("urn:globus:groups:id:449718d5-32b2-48ba-bd46-e045deab5430", False),
        # -- Error Cases --
        # Username
        ("foo@globus.org", True),
        # Identity URN
        ("urn:globus:auth:identity:64831427-e501-420b-93da-9e4efee3dd51", True),
    ),
)
def test_resolve_principal_urn__when_principal_type_is_group(principal, expect_error):
    """
    Verifies success & error cases for principal resolution when principal_type is
      explicitly set to "group".
    """
    # === Setup ===
    auth_client = unittest.mock.Mock(spec=CustomAuthClient)

    try:
        # === Act ===
        urn = resolve_principal_urn(
            auth_client=auth_client,
            principal=principal,
            principal_type="group",
        )
    except click.UsageError as e:
        # === Verify (Error Case) ===
        assert expect_error
        assert e.message == (
            f"'--principal-type group' but '{principal}' is not a valid group UUID or "
            "URN"
        )
    else:
        # === Verify (Success Case) ===
        assert not expect_error
        assert urn == "urn:globus:groups:id:449718d5-32b2-48ba-bd46-e045deab5430"


def test_resolve_principal_urn__when_principal_type_key_is_non_default():
    auth_client = unittest.mock.Mock(spec=CustomAuthClient)

    with pytest.raises(click.UsageError) as e:
        resolve_principal_urn(
            auth_client=auth_client,
            principal="urn:globus:groups:id:449718d5-32b2-48ba-bd46-e045deab5430",
            principal_type="identity",
            principal_type_key="--foobarjohn",
        )

    assert e.value.message.startswith("'--foobarjohn identity' but")


def test_lazy_dict():
    real_dict = {"a": 1, "b": 2}
    lazy_dict = LazyDict(real_dict)

    assert "c" not in lazy_dict
    assert real_dict == lazy_dict

    lazy_dict.register_loader("c", lambda: 3)

    assert "c" in lazy_dict
    assert real_dict == lazy_dict

    assert lazy_dict["c"] == 3
    assert real_dict != lazy_dict


def test_lazy_dict_only_loads_once():
    load_call_count = 0

    def load_data():
        nonlocal load_call_count
        load_call_count += 1
        return 3

    lazy_dict = LazyDict()
    lazy_dict.register_loader("c", load_data)

    assert load_call_count == 0

    assert lazy_dict["c"] == 3
    assert load_call_count == 1

    assert lazy_dict["c"] == 3
    assert lazy_dict.get("c") == 3
    assert load_call_count == 1


def test_lazy_dict_excludes_loaders_from_presentation_until_loaded():
    lazy_dict = LazyDict({"a": 1, "b": 2})
    lazy_dict.register_loader("c", lambda: 3)

    assert "3" not in repr(lazy_dict)
    assert "3" not in str(lazy_dict)

    lazy_dict["c"]

    assert "3" in repr(lazy_dict)
    assert "3" in str(lazy_dict)


def test_lazy_dict_prefers_explicit_values_to_loaders():
    lazy_dict = LazyDict({"a": 1, "b": 2})
    lazy_dict.register_loader("a", lambda: 3)

    assert lazy_dict["a"] == 1

    lazy_dict["a"] = 4

    assert lazy_dict["a"] == 4
    assert lazy_dict.get("a") == 4


def test_lazy_dict_delete_removes_unloaded_loaders():
    lazy = LazyDict({"a": 1})
    lazy.register_loader("a", lambda: 1)
    lazy.register_loader("b", lambda: 2)

    assert "a" in lazy
    assert "b" in lazy

    del lazy["a"]
    del lazy["b"]

    assert "a" not in lazy
    assert "b" not in lazy
