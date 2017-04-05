from distutils.version import LooseVersion

# single source of truth for package version,
# see https://packaging.python.org/en/latest/single_source_version/

# The Globus CLI version *always* starts with the version of the SDK which it
# depends upon. If necessary, we do additional point releases upon the SDK
# version.
# For example, if the SDK version is
#       2.4.6
# then the following are valid CLI versions:
#       2.4.6.0
#       2.4.6.1
#       2.4.6.10
#       2.4.6.99
# and the following invalid CLI versions:
#       2.4.6       -- doesn't specify point release
#       2.4.7.0     -- should depend on SDK 2.4.7
#       2.4.6.1.2   -- no additional point versions
#       0.1.0.0     -- no special rules for things like this
#       1.4.6.0     -- differing major version, obviously wrong
__version__ = "0.7.1.0"

# app name to send as part of SDK requests
app_name = 'Globus CLI v{} - Beta'.format(__version__)


# pull down version data from PyPi
def get_versions():
    """
    Wrap in a function to ensure that we don't run this every time a CLI
    command runs (yuck!)

    Also protects import of `requests` from issues when grabbed by setuptools.
    More on that inline
    """
    # import in the func (rather than top-level scope) so that at setup time,
    # `requests` isn't required -- otherwise, setuptools will fail to run
    # because requests isn't installed yet.
    import requests
    try:
        version_data = requests.get(
            'https://pypi.python.org/pypi/globus-cli/json').json()
        latest = max(LooseVersion(v) for v in version_data['releases'])
        return latest, LooseVersion(__version__)
    # if the fetch from pypi fails
    except requests.RequestException:
        return None, LooseVersion(__version__)
