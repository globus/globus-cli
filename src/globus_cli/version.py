from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from packaging.version import Version

# single source of truth for package version,
# see https://packaging.python.org/en/latest/single_source_version/
__version__ = "3.39.0"

# app name to send as part of SDK requests
app_name = f"Globus CLI v{__version__}"


# pull down version data from PyPi
def get_versions() -> tuple[Version | None, Version]:
    """
    Wrap in a function to ensure that we don't run this every time a CLI
    command runs or when version number is loaded by setuptools.

    Returns a pair: (latest_version, current_version)
    """
    # import in the func (rather than top-level scope) so that at setup time,
    # libraries aren't required -- otherwise, setuptools will fail to run
    # because these packages aren't installed yet.
    import requests
    from packaging.version import Version

    try:
        response = requests.get("https://pypi.python.org/pypi/globus-cli/json")
    # if the fetch from pypi fails
    except requests.RequestException:
        return None, Version(__version__)
    parsed_versions = [Version(v) for v in response.json()["releases"]]
    latest = max(parsed_versions)
    return latest, Version(__version__)
