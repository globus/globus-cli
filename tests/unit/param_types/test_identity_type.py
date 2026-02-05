import base64
import textwrap
import uuid

import click
import pytest

from globus_cli.parsing import IdentityType, ParsedIdentity


@pytest.fixture
def b32_encoded_id():
    x = uuid.uuid4()

    b32_str = base64.b32encode(x.bytes).decode().rstrip("=")

    return str(x), f"u_{b32_str}"


@pytest.fixture
def make_print_command():
    def func(param_type):
        @click.command()
        @click.argument("i", type=param_type)
        def cmd(i):
            assert isinstance(i, ParsedIdentity)
            click.echo(f"value={i.value!r}")
            click.echo(f"idtype={i.idtype!r}")

        return cmd

    return func


def test_identity_type_default_allows_username(runner, make_print_command):
    cmd = make_print_command(IdentityType())
    result = runner.invoke(cmd, ["globus@globus.org"])

    assert result.exit_code == 0
    assert result.output == textwrap.dedent("""\
        value='globus@globus.org'
        idtype='username'
        """)


def test_identity_type_default_allows_id(runner, make_print_command):
    user_id = str(uuid.uuid4())
    cmd = make_print_command(IdentityType())
    result = runner.invoke(cmd, [user_id])

    assert result.exit_code == 0
    assert result.output == textwrap.dedent(f"""\
        value='{user_id}'
        idtype='identity'
        """)


def test_identity_type_default_rejects_domain(runner, make_print_command):
    cmd = make_print_command(IdentityType())
    result = runner.invoke(cmd, ["uchicago.edu"])

    assert result.exit_code == 2
    assert "'uchicago.edu' does not appear to be a valid identity" in result.output


def test_identity_type_allows_domain_if_configured(runner, make_print_command):
    cmd = make_print_command(IdentityType(allow_domains=True))
    result = runner.invoke(cmd, ["uchicago.edu"])

    assert result.exit_code == 0
    assert result.output == textwrap.dedent("""\
        value='uchicago.edu'
        idtype='domain'
        """)


def test_identity_type_default_rejects_b32_encoded_ids(
    runner, make_print_command, b32_encoded_id
):
    _, b32_variant = b32_encoded_id
    cmd = make_print_command(IdentityType())
    result = runner.invoke(cmd, [b32_variant])

    assert result.exit_code == 2
    assert f"'{b32_variant}' does not appear to be a valid identity" in result.output


def test_identity_type_allows_b32_encoded_ids_if_configured(
    runner, make_print_command, b32_encoded_id
):
    decoded, b32_variant = b32_encoded_id
    cmd = make_print_command(IdentityType(allow_b32_usernames=True))
    result = runner.invoke(cmd, [b32_variant])

    assert result.exit_code == 0
    assert result.output == textwrap.dedent(f"""\
        value='{decoded}'
        idtype='identity'
        """)


@pytest.mark.parametrize(
    "transform",
    [
        pytest.param(lambda x: x[2:], id="missing_prefix"),
        pytest.param(lambda x: x[:-1], id="wrong_length"),
        pytest.param(lambda _: "u_" + ("x" * 24), id="non_uuid_bytes"),
    ],
)
def test_identity_type_rejects_malformed_b32_encoded_ids(
    transform, runner, make_print_command, b32_encoded_id
):
    _, b32_variant = b32_encoded_id
    input_id = transform(b32_variant)

    cmd = make_print_command(IdentityType(allow_b32_usernames=True))
    result = runner.invoke(cmd, [input_id])

    assert result.exit_code == 2
    assert f"'{input_id}' does not appear to be a valid identity" in result.output
