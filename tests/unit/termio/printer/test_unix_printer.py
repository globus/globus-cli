from io import StringIO

import click
import pytest

from globus_cli.termio.printers import UnixPrinter


def _format_output(outputs: list[list[str]]) -> str:
    return "\n".join("\t".join(x) for x in outputs) + "\n"


@pytest.fixture
def print_data(click_context):
    def func(data):
        printer = UnixPrinter()

        with StringIO() as stream:
            with click_context():
                printer.echo(data, stream)
            result = stream.getvalue()

        return result

    return func


@pytest.mark.parametrize(
    "scalar_input, formatted_scalar",
    (
        (1, "1"),
        (-1, "-1"),
        (1.0, "1.0"),
        ("1.1", "1.1"),
        ("foo", "foo"),
        (True, "True"),
        (False, "False"),
        (None, "None"),
    ),
)
def test_scalar(print_data, scalar_input, formatted_scalar):
    result = print_data(scalar_input)
    expect_output = f"{formatted_scalar}\n"
    assert result == expect_output


def test_scalar_list(print_data):
    mixed_scalar_list = [1, "foo", 2, False]
    expect_output = _format_output(
        [
            ["1", "foo", "2", "False"],
        ]
    )
    result = print_data(mixed_scalar_list)

    assert result == expect_output


def test_empty_list_produces_no_output(print_data):
    # This is a long-standing, if odd, behavior -- the test ensures that we remain
    # consistent unless we decide that we intentionally want to change this
    result = print_data([])
    assert result == ""


def test_list_of_dicts(print_data):
    data = [
        {"foo": 1, "bar": 2},
        {"foo": 200, "bar": 303},
    ]
    expect_output = _format_output(
        [
            ["2", "1"],
            ["303", "200"],
        ]
    )

    result = print_data(data)
    assert result == expect_output


def test_mixed_list_of_dicts_errors(print_data, capfd):
    data = [{"foo": 1, "bar": 2}, "foo-bar"]

    with pytest.raises(click.exceptions.Exit) as excinfo:
        print_data(data)

    assert excinfo.value.exit_code == 2

    captured = capfd.readouterr()
    assert (
        "Formatter cannot handle arrays which mix JSON objects with other datatypes."
    ) in captured.err


def test_list_of_lists(print_data):
    data = [
        ["foo", "bar"],
        ["baz"],
    ]
    expect_output = _format_output(
        [
            ["foo", "bar"],
            ["baz"],
        ]
    )
    result = print_data(data)
    assert result == expect_output


def test_mixed_list_of_lists(print_data):
    data = [
        "alpha",
        ["foo", "bar"],
        "beta",
        ["baz", "bar"],
    ]
    # scalars come out first, on one line, then the nested lists on separate lines
    expect_output = _format_output(
        [
            ["alpha", "beta"],
            ["foo", "bar"],
            ["baz", "bar"],
        ]
    )

    result = print_data(data)
    assert result == expect_output


def test_mixed_dict(print_data):
    data = {
        "x": 3,
        "y": 8,
        "labels": ["foo", "bar"],
    }
    # like lists, scalars come out first, on one line
    # followed by the nested datastructures
    # in this case, an 'identifier' label is applied to each element
    expect_output = _format_output(
        [
            ["3", "8"],
            ["LABELS", "foo"],
            ["LABELS", "bar"],
        ]
    )

    result = print_data(data)
    assert result == expect_output


def test_list_of_inconsistent_dicts(print_data, capfd):
    # this errors because we try to detect which keys map to scalars,
    # but then the data betrays us by not matching that mapping
    data = [
        {
            "x": 3,
            "y": 8,
        },
        {"x": ["3"], "y": {"z": 1}},
    ]

    with pytest.raises(click.exceptions.Exit) as excinfo:
        print_data(data)

    assert excinfo.value.exit_code == 2

    captured = capfd.readouterr()
    assert (
        "Error during UNIX formatting of response data. "
        "Lists where key-value mappings are not uniformly scalar or non-scalar "
        "are not supported."
    ) in captured.err


def test_list_of_dicts_with_surprising_object(print_data, capfd):
    # similar to inconsistent data, an unexpected object can go boom
    kaboom = object()
    data = [
        {
            "x": 3,
            "info": {"foo": "bar"},
        },
        {
            "x": 3,
            "info": kaboom,
        },
    ]

    with pytest.raises(click.exceptions.Exit) as excinfo:
        print_data(data)

    assert excinfo.value.exit_code == 2

    captured = capfd.readouterr()
    assert (
        "Error during UNIX formatting of response data. "
        "Lists where key-value mappings are not uniformly scalar or non-scalar "
        "are not supported."
    ) in captured.err


def test_list_of_dicts_containing_malicious_dict_like(print_data, capfd):
    # this test really exercises a corner case in the implementation
    # it's not possible to get some key to be mis-detected as a dict when it's
    # really a scalar, but you *can* construct a badly behaved object which
    # tricks the detection logic

    first_call = True

    class OpenlyMaliciousDict(dict):
        def items(self):
            nonlocal first_call
            if first_call:
                first_call = False
                return ()
            return super().items()

    # crazy_item will not show that it contains a scalar value 'x' on first pass, but
    # it really does have one if you ask it again
    crazy_item = OpenlyMaliciousDict(x=1)

    data = [
        {
            "x": {"foo": "bar"},
        },
        crazy_item,
    ]

    with pytest.raises(click.exceptions.Exit) as excinfo:
        print_data(data)

    assert excinfo.value.exit_code == 2

    captured = capfd.readouterr()
    assert (
        "Error during UNIX formatting of response data. "
        "Lists where key-value mappings are not uniformly scalar or non-scalar "
        "are not supported."
    ) in captured.err


def test_dict_with_missing_values_treated_as_null(print_data):
    data = [
        {"x": 3, "y": 1, "z": 5},
        {"x": 100, "y": 200},
    ]
    expect_output = _format_output(
        [
            ["3", "1", "5"],
            ["100", "200", "None"],
        ]
    )

    result = print_data(data)
    assert result == expect_output
