import atexit
import os
import site
import subprocess
import sys

import click

from globus_cli.parsing import command
from globus_cli.version import get_versions


# check if the source for this is inside of the USER_BASE
# if so, a `pip install --user` was used
# https://docs.python.org/3/library/site.html#site.getuserbase
def _is_user_install() -> bool:
    # under old versions of virtualenv, `getuserbase` is not included in the generated
    # `site.py` which gets injected into the virtualenv
    # therefore, if the `site` module has no such method, immediately fail
    # (virtualenv != "user install")
    if not hasattr(site, "getuserbase"):
        return False
    return __file__.startswith(site.getuserbase())


# check if the source is in the PIPX home, which would mean that this is a pipx install
# (even if it is in the userbase dir)
# pipx home discovery extracted from pipx itself. see:
#   https://github.com/pypa/pipx/blob/878f03504417fa4cc9a6676b1bc24aef2ba3e491/src/pipx/constants.py#L8
def _is_pipx_install() -> bool:
    import pathlib

    _DEFAULT_PIPX_HOME = pathlib.Path.home() / ".local/pipx"
    _PIPX_HOME = pathlib.Path(os.getenv("PIPX_HOME", _DEFAULT_PIPX_HOME)).resolve()
    return __file__.startswith(str(_PIPX_HOME))


def _call_pip(*args: str) -> None:
    """
    Invoke pip *safely* and in the *supported* way:
    https://pip.pypa.io/en/latest/user_guide/#using-pip-from-your-program
    """
    all_args = [sys.executable, "-m", "pip"] + list(args)
    print("> {}".format(" ".join(all_args)))
    subprocess.check_call(all_args)


def _check_pip_installed() -> bool:
    """
    Invoke `pip --version` and make sure it doesn't error.
    Use check_output to capture stdout and stderr

    Invokes pip by the same manner that we plan to in _call_pip()

    Don't bother trying to reuse _call_pip to do this... Finnicky and not worth
    the effort.
    """
    try:
        subprocess.check_output(
            [sys.executable, "-m", "pip", "--version"], stderr=subprocess.STDOUT
        )
        return True
    except subprocess.CalledProcessError:
        return False


@command(
    "update",
    disable_options=["format", "map_http_status"],
    short_help="Update the Globus CLI to its latest version",
)
@click.option("--force", is_flag=True, hidden=True)
@click.option("--yes", is_flag=True, help='Automatically say "yes" to all prompts')
def update_command(yes: bool, force: bool) -> None:
    """Update the Globus CLI to its latest version.

    The *globus update* command checks if a more recent version of the Globus CLI
    is available on PyPi, and if so asks for user consent to update to the most
    recent version available.
    """
    # enforce that pip MUST be installed
    # Why not just include it in the setup.py requirements? Mostly weak
    # reasons, but it shouldn't matter much.
    # - if someone has installed the CLI without pip, then they haven't
    #   followed our install instructions, so it's mostly a non-issue
    # - we don't want to have `pip install -U globus-cli` upgrade pip -- that's
    #   a little bit invasive and easy to do by accident on modern versions of
    #   pip where `--upgrade-strategy` defaults to `eager`
    # - we may want to do distributions in the future with dependencies baked
    #   into a package, but we'd never want to do that with pip. More changes
    #   would be needed to support that use-case, which we've discussed, but
    #   not depending directly on pip gives us a better escape hatch
    # - if we depend on pip, we need to start thinking about what versions we
    #   support. In point of fact, that becomes an issue as soon as we add this
    #   command, but not being explicit about it lets us punt for now (maybe
    #   indefinitely) on figuring out version requirements. All of that is to
    #   say: not including it is bad, and from that badness we reap the rewards
    #   of procrastination and non-explicit requirements
    # - Advanced usage, like `pip install -t` can produce an installed version
    #   of the CLI which can't import its installing `pip`. If we depend on
    #   pip, anyone doing this is forced to get two copies of pip, which seems
    #   kind of nasty (even if "they're asking for it")
    if not _check_pip_installed():
        click.echo("`globus update` requires pip. Please install pip and try again")
        click.get_current_context().exit(1)

    # lookup version from PyPi, abort if we can't get it
    latest, current = get_versions()
    if latest is None:
        click.echo("Failed to lookup latest version. Aborting.")
        click.get_current_context().exit(1)

    # in the case where we're already up to date, do nothing and exit
    if current == latest:
        click.echo(f"You are already running the latest version: {current}")
        if not force:
            return
        else:
            click.echo("continuing with update (--force)")

    # show the version(s) and prompt to continue
    click.echo(f"You are running version {current}\nThe latest version is {latest}")
    if not (yes or force or click.confirm("Continue with the upgrade?", default=True)):
        click.get_current_context().exit(1)

    # if we make it through to here, it means we didn't hit any safe (or
    # unsafe) abort conditions, so set the target version for upgrade to
    # the latest
    target_version = f"globus-cli=={latest}"

    # print verbose warning/help message, to guide less fortunate souls who hit
    # Ctrl+C at a foolish time, lose connectivity, or don't invoke with `sudo`
    # on a global install of the CLI
    click.echo(
        (
            "The Globus CLI will now update itself.\n"
            "In the event that an error occurs or the update is interrupted, we "
            "recommend uninstalling and reinstalling the CLI.\n"
            "Update Target: {}\n"
        ).format(target_version)
    )

    # register the upgrade activity as an atexit function
    # this ensures that most library teardown (other than whatever libs might
    # jam into atexit themselves...) has already run, and therefore protects us
    # against most potential bugs resulting from upgrading click while a click
    # command is running
    #
    # NOTE: there is a risk that we will see bugs on upgrade if the act of
    # doing a pip upgrade install changes state on disk and we (or a lib we
    # use) rely on that via pkg_resources, lazy/deferred imports, or good
    # old-fashioned direct inspection of `__file__` and the like DURING an
    # atexit method. Anything outside of atexit methods remains safe!
    @atexit.register
    def do_upgrade() -> None:
        install_args = ["install", "--upgrade", target_version]
        if _is_user_install() and not _is_pipx_install():
            install_args.insert(1, "--user")
        _call_pip(*install_args)
