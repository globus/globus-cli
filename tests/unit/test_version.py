from distutils.version import LooseVersion

import pytest
import requests
import responses

import globus_cli.version


@pytest.mark.parametrize(
    "injected_version, expected",
    (
        ("0.0.0", globus_cli.version.__version__),
        ("1000.1000.1000", "1000.1000.1000"),
    ),
)
@pytest.mark.filterwarnings("ignore:distutils Version classes are deprecated")
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
        LooseVersion(expected),
        LooseVersion(globus_cli.version.__version__),
    )


@pytest.mark.filterwarnings("ignore:distutils Version classes are deprecated")
def test_get_versions_failure():
    responses.add(
        "GET",
        "https://pypi.python.org/pypi/globus-cli/json",
        body=requests.RequestException(),
    )
    assert globus_cli.version.get_versions() == (
        None,
        LooseVersion(globus_cli.version.__version__),
    )
