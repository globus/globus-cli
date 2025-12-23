from __future__ import annotations

import importlib.metadata
import platform
import site
import sys
import typing as t

import click

from globus_cli.parsing import command
from globus_cli.termio import is_verbose, verbosity
from globus_cli.version import get_versions

if t.TYPE_CHECKING:
    from packaging.version import Version


def _get_package_data() -> list[list[str]]:
    """
    Import a set of important packages and return relevant data about them in a
    dict.
    Imports are done in here to avoid potential for circular imports and other
    problems, and to make iteration simpler.
    """
    moddata = []
    modlist: tuple[str, ...] = (
        "click",
        "cryptography",
        "globus_cli",
        "globus_sdk",
        "jmespath",
        "requests",
    )
    if verbosity() < 2:
        modlist = ("globus_cli", "globus_sdk", "requests")

    for mod in modlist:
        cur = [mod]
        try:
            loaded_mod = __import__(mod)
        except ImportError:
            loaded_mod = None

        for attr in ("__version__", "__file__", "__path__"):
            # if loading failed, be sure to pad with error messages
            if loaded_mod is None:
                cur.append("[import failed]")
                continue
            elif attr == "__version__":
                version = importlib.metadata.distribution(mod).version
                cur.append(version)
                continue

            try:
                attrval = getattr(loaded_mod, attr)
            except AttributeError:
                attrval = ""
            cur.append(attrval)
        moddata.append(cur)

    return moddata


def _get_versionblock_message(current: Version, latest: Version) -> str:
    return f"""\
Installed version:  {current}
Latest version:     {latest}"""


def _get_post_message(current: Version, latest: Version) -> str:
    if current == latest:
        return "You are running the latest version of the Globus CLI"
    if current > latest:
        return "You are running a preview version of the Globus CLI"
    return "You should update your version of the Globus CLI with\n  globus update"


@command(
    "version",
    disable_options=["format", "map_http_status"],
    short_help="Show the version and exit.",
)
def version_command() -> None:
    """
    Displays the current and latest versions of the Globus CLI.

    If the current version is not the latest version, instructions will be given
    for how to update the CLI.
    """
    latest, current = get_versions()
    if latest is None:
        click.echo(f"Installed Version: {current}\nFailed to lookup latest version.")
    else:
        click.echo(
            _get_versionblock_message(current, latest)
            + "\n\n"
            + _get_post_message(current, latest)
        )

    # verbose shows more platform and python info
    # it also includes versions of some CLI dependencies
    if is_verbose():
        moddata = _get_package_data()

        click.echo("\nVerbose Data\n---")

        click.echo("platform:")
        click.echo(f"  platform: {platform.platform()}")
        click.echo(f"  py_implementation: {platform.python_implementation()}")
        click.echo(f"  py_version: {platform.python_version()}")
        click.echo(f"  sys.executable: {sys.executable}")
        click.echo(f"  site.USER_BASE: {site.USER_BASE}")

        click.echo("modules:")
        for mod, modversion, modfile, modpath in moddata:
            click.echo(f"  {mod}:")
            click.echo(f"    __version__: {modversion}")
            click.echo(f"    __file__: {modfile}")
            click.echo(f"    __path__: {modpath}")
