import importlib.metadata
import textwrap

import pytest
import responses


def fmt_mod_info(modname):
    mod = __import__(modname)
    ver = importlib.metadata.distribution(modname).version
    filepath, syspath = mod.__file__, mod.__path__

    return textwrap.dedent(
        f"""\
        {modname}:
          __version__: {ver}
          __file__: {filepath}
          __path__: {syspath}
        """
    )


@pytest.fixture(scope="session")
def installed_cli_version():
    return importlib.metadata.distribution("globus_cli").version


@pytest.fixture
def mock_pypi_version():
    def func(version):
        responses.get(
            url="https://pypi.python.org/pypi/globus-cli/json",
            json={"releases": [version]},
        )

    return func


def test_version_command_on_latest(run_line, mock_pypi_version, installed_cli_version):
    mock_pypi_version(installed_cli_version)

    result = run_line("globus version")
    assert result.output == textwrap.dedent(
        f"""\
        Installed version:  {installed_cli_version}
        Latest version:     {installed_cli_version}

        You are running the latest version of the Globus CLI
        """
    )


def test_version_command_on_preview(run_line, mock_pypi_version, installed_cli_version):
    mock_pypi_version("1.0")

    result = run_line("globus version")
    assert result.output == textwrap.dedent(
        f"""\
        Installed version:  {installed_cli_version}
        Latest version:     1.0

        You are running a preview version of the Globus CLI
        """
    )


def test_version_command_newer_available(
    run_line, mock_pypi_version, installed_cli_version
):
    major = int(installed_cli_version.partition(".")[0])
    latest = f"{major+1}.0"
    mock_pypi_version(latest)

    result = run_line("globus version")
    assert result.output == textwrap.dedent(
        f"""\
        Installed version:  {installed_cli_version}
        Latest version:     {latest}

        You should update your version of the Globus CLI with
          globus update
        """
    )


def test_verbose_version_command_shows_related_package_versions(
    run_line, mock_pypi_version, installed_cli_version
):
    mock_pypi_version(installed_cli_version)

    result = run_line("globus version -v")

    # TODO: do more to validate this output
    for modname in (
        "globus_cli",
        "globus_sdk",
        "requests",
    ):
        assert textwrap.indent(fmt_mod_info(modname), "  ") in result.output

    assert "click" not in result.output
    assert "cryptography" not in result.output
    assert "jmespath" not in result.output


def test_very_verbose_version_command_shows_more_related_package_versions(
    run_line, mock_pypi_version, installed_cli_version
):
    mock_pypi_version(installed_cli_version)

    result = run_line("globus version -vv")
    for modname in (
        "click",
        "cryptography",
        "globus_cli",
        "globus_sdk",
        "jmespath",
        "requests",
    ):
        assert textwrap.indent(fmt_mod_info(modname), "  ") in result.output
