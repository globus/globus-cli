from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from distutils.version import LooseVersion

# single source of truth for package version,
# see https://packaging.python.org/en/latest/single_source_version/
__version__ = "3.5.0"

# app name to send as part of SDK requests
app_name = f"Globus CLI v{__version__}"


# pull down version data from PyPi
def get_versions() -> Tuple[Optional["LooseVersion"], "LooseVersion"]:
    """
    Wrap in a function to ensure that we don't run this every time a CLI
    command runs or when version number is loaded by setuptools.

    Returns a pair: (latest_version, current_version)
    """
    # import in the func (rather than top-level scope) so that at setup time,
    # `requests` isn't required -- otherwise, setuptools will fail to run
    # because it isn't installed yet.
    from distutils.version import LooseVersion

    import requests

    try:
        version_data = requests.get(
            "https://pypi.python.org/pypi/globus-cli/json"
        ).json()
        parsed_versions = [LooseVersion(v) for v in version_data["releases"]]
        latest = max(parsed_versions)
        return latest, LooseVersion(__version__)
    # if the fetch from pypi fails
    except requests.RequestException:
        return None, LooseVersion(__version__)
