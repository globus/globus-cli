from __future__ import annotations

import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager, is_remote_session
from globus_cli.parsing import command, endpoint_id_arg, mutex_option_group
from globus_cli.termio import display


@command("activate", deprecated=True, hidden=True)
@endpoint_id_arg
@click.option(
    "--web",
    is_flag=True,
    default=False,
    help="Use web activation. Mutually exclusive with --myproxy.",
)
@click.option(
    "--no-browser",
    is_flag=True,
    default=False,
    help=(
        "If using --web, Give a url to manually follow instead of "
        "opening your default web browser. Implied if the CLI "
        "detects this is a remote session."
    ),
)
@click.option(
    "--myproxy",
    is_flag=True,
    default=False,
    help="Use myproxy activation. Mutually exclusive with --web.",
)
@click.option(
    "--myproxy-username",
    "-U",
    help="Give a username to use with --myproxy",
)
@click.option("--myproxy-password", "-P", hidden=True)
@click.option(
    "--myproxy-lifetime",
    type=int,
    help=(
        "The lifetime for the credential to request from the "
        "server under --myproxy activation, in hours. "
        "The myproxy server may be configured with a maximum "
        "lifetime which it will use if this value is too high"
    ),
)
@click.option(
    "--no-autoactivate",
    is_flag=True,
    default=False,
    help=(
        "Don't attempt to autoactivate endpoint before using "
        "another activation method."
    ),
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force activation even if endpoint is already activated.",
)
@mutex_option_group("--web", "--myproxy")
@LoginManager.requires_login("transfer")
def endpoint_activate(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    myproxy: bool,
    myproxy_username: str | None,
    myproxy_password: str | None,
    myproxy_lifetime: int | None,
    web: bool,
    no_browser: bool,
    no_autoactivate: bool,
    force: bool,
) -> None:
    """
    Activate an endpoint using Autoactivation, Myproxy, Delegate Proxy,
    or Web activation.
    Note that --web and --myproxy activation are mutually
    exclusive options.

    \b
    Autoactivation will always be attempted unless the --no-autoactivate
    option is given. If autoactivation succeeds any other activation options
    will be ignored as the endpoint has already been successfully activated.

    \b
    To use Web activation use the --web option.
    The CLI will try to open your default browser to the endpoint's activation
    page, but if a remote CLI session is detected, or the --no-browser option
    is given, a url will be printed for you to manually follow and activate
    the endpoint.

    \b
    To use Myproxy activation give the --myproxy option.
    Myproxy activation requires your username and password for the myproxy
    server the endpoint is using for authentication. e.g. for default
    Globus Connect Server endpoints this will be your login credentials for the
    server the endpoint is hosted on.
    You can enter your username when prompted or give your username with the
    --myproxy-username option.
    For security it is recommended that you only enter your password when
    prompted to hide your inputs and keep your password out of your
    command history, but you may pass your password with the hidden
    --myproxy-password or -P options.
    """
    from globus_cli.services.transfer import activation_requirements_help_text

    transfer_client = login_manager.get_transfer_client()

    # validate options
    if no_autoactivate and not (myproxy or web):
        raise click.UsageError(
            "--no-autoactivate requires another activation method be given."
        )
    if myproxy_username and not myproxy:
        raise click.UsageError("--myproxy-username requires --myproxy.")
    if myproxy_password and not myproxy:
        raise click.UsageError("--myproxy-password requires --myproxy.")
    # NOTE: "0" is a legitimate, though weird, value
    # In the case where someone is setting this value programmatically,
    # respecting it behaves more consistently/predictably
    if myproxy_lifetime is not None and not myproxy:
        raise click.UsageError("--myproxy-lifetime requires --myproxy.")
    if no_browser and not web:
        raise click.UsageError("--no-browser requires --web.")

    # check if endpoint is already activated unless --force
    if not force:
        res: dict[str, str] | globus_sdk.GlobusHTTPResponse = (
            transfer_client.endpoint_autoactivate(endpoint_id, if_expires_in=60)
        )

        if "AlreadyActivated" == res["code"]:
            display(
                res,
                simple_text=(
                    "Endpoint is already activated. Activation "
                    "expires at {}".format(res["expire_time"])
                ),
            )
            return

    # attempt autoactivation unless --no-autoactivate
    if not no_autoactivate:
        res = transfer_client.endpoint_autoactivate(endpoint_id)

        if "AutoActivated" in res["code"]:
            display(
                res,
                simple_text=(
                    "Autoactivation succeeded with message: {}".format(res["message"])
                ),
            )
            return

        # override potentially confusing autoactivation failure response
        else:
            message = (
                "The endpoint could not be auto-activated.\n\n"
                + activation_requirements_help_text(res, endpoint_id)
            )
            res = {"message": message}

    # myproxy activation
    if myproxy:
        # fetch activation requirements
        requirements_data = transfer_client.endpoint_get_activation_requirements(
            endpoint_id
        ).data
        # filter to the myproxy requirements; ensure that there are values
        myproxy_requirements_data = [
            x for x in requirements_data["DATA"] if x["type"] == "myproxy"
        ]
        if not len(myproxy_requirements_data):
            raise click.ClickException(
                "This endpoint does not support myproxy activation"
            )

        # get username and password
        if not myproxy_username:
            myproxy_username = click.prompt("Myproxy username")
        if not myproxy_password:
            myproxy_password = click.prompt("Myproxy password", hide_input=True)

        # fill out the requirements data -- note that because everything has been done
        # by reference, `requirements_data` still refers to the document containing
        # these values
        for data in myproxy_requirements_data:
            if data["name"] == "passphrase":
                data["value"] = myproxy_password
            if data["name"] == "username":
                data["value"] = myproxy_username
            if data["name"] == "hostname" and data["value"] is None:
                raise click.ClickException(
                    "This endpoint has no myproxy server "
                    "and so cannot be activated through myproxy"
                )
            # NOTE: remember that "0" is a possible value
            if data["name"] == "lifetime_in_hours" and myproxy_lifetime is not None:
                data["value"] = str(myproxy_lifetime)

        res = transfer_client.endpoint_activate(
            endpoint_id, requirements_data=requirements_data
        )

    # web activation
    elif web:
        import webbrowser

        from globus_sdk.config import get_webapp_url

        url = f"{get_webapp_url()}file-manager?origin_id={endpoint_id}"
        if no_browser or is_remote_session():
            res = {"message": f"Web activation url: {url}", "url": url}
        else:
            webbrowser.open(url, new=1)
            res = {"message": "Browser opened to web activation page", "url": url}

    # output
    display(res, text_mode=display.RAW, response_key="message")
