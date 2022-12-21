"""
This is a self-test for utilities in the testsuite:
 - check_has_correct_annotations_for_click_args
 - deduce_type_from_parameter
"""
import sys

import click
import pytest

from globus_cli.constants import ExplicitNullType
from globus_cli.parsing.param_types import JSONStringOrFile, StringOrNull
from globus_cli.types import JsonValue
from tests.click_types import (
    check_has_correct_annotations_for_click_args,
    deduce_type_from_parameter,
)

if sys.version_info < (3, 10):
    pytest.skip(
        "skipping click type deduction tests on python < 3.10", allow_module_level=True
    )


def test_deduce_type_from_parameter_on_non_nullable_flag():
    opt = click.Option(["--foo/--no-foo"], is_flag=True)
    assert deduce_type_from_parameter(opt) == bool


def test_deduce_type_from_parameter_on_nullable_flag():
    opt = click.Option(["--foo/--no-foo"], is_flag=True, default=None)
    assert deduce_type_from_parameter(opt) == (bool | None)


def test_deduce_type_from_multiple_string_opt():
    opt = click.Option(["--foo"], multiple=True)
    assert deduce_type_from_parameter(opt) == tuple[str, ...]


def test_deduce_type_from_string_or_null_opt():
    opt = click.Option(["--foo"], type=StringOrNull())
    assert deduce_type_from_parameter(opt) == (str | ExplicitNullType | None)


def test_deduce_type_from_multiple_string_or_null_opt():
    opt = click.Option(["--foo"], multiple=True, type=StringOrNull())
    assert deduce_type_from_parameter(opt) == tuple[str | ExplicitNullType, ...]


def test_deduce_type_from_int_argument():
    arg = click.Argument(["FOO"], type=int)
    assert deduce_type_from_parameter(arg) == int


def test_deduce_type_from_json_string_or_file():
    arg = click.Argument(["FOO"], type=JSONStringOrFile())
    assert deduce_type_from_parameter(arg) == JsonValue


def test_deduce_type_from_nargs_many_argument():
    arg = click.Argument(["FOO"], nargs=-1)
    assert deduce_type_from_parameter(arg) == tuple[str, ...]


def test_check_annotations_fails_on_missing_arg():
    @click.command
    @click.option("--foo")
    def mycmd():
        pass

    with pytest.raises(
        ValueError, match="expected parameter 'foo' was not in type hints"
    ):
        check_has_correct_annotations_for_click_args(mycmd)


def test_check_annotations_fails_on_bad_arg_type():
    @click.command
    @click.option("--foo")
    def mycmd(foo: int):
        pass

    with pytest.raises(
        ValueError, match="parameter 'foo' has unexpected parameter type"
    ):
        check_has_correct_annotations_for_click_args(mycmd)
