import pytest
import requests
import responses
from packaging.version import Version

import globus_cli.version


@pytest.mark.parametrize(
    "injected_version, expected",
    (
        ("0.0.0", globus_cli.version.__version__),
        ("1000.1000.1000", "1000.1000.1000"),
    ),
)
def test_get_versions_success(injected_version, expected):
    # Only a portion of the PyPI response is needed.
    pypi_json_response = {
        "releases": {
            injected_version: [],
            globus_cli.version.__version__: [],
        }
    }
    responses.add(
        "GET", "https://pypi.python.org/pypi/globus-cli/json", json=pypi_json_response
    )
    assert globus_cli.version.get_versions() == (
        Version(expected),
        Version(globus_cli.version.__version__),
    )


def test_get_versions_failure():
    responses.add(
        "GET",
        "https://pypi.python.org/pypi/globus-cli/json",
        body=requests.RequestException(),
    )
    assert globus_cli.version.get_versions() == (
        None,
        Version(globus_cli.version.__version__),
    )
