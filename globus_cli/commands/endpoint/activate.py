import click
import webbrowser

from globus_cli.parsing import common_options, endpoint_id_arg, HiddenOption
from globus_cli.safeio import OutputFormatter
from globus_cli.config import lookup_option, MYPROXY_USERNAME_OPTNAME
from globus_cli.services.transfer import get_client
from globus_cli.helpers import is_remote_session


@click.command("activate",
               short_help="Activate an endpoint",
               help="""
    Activate an endpoint using Autoactivation, Myproxy, or Web activation.
    Note that --web and --myproxy activation are mutually exclusive options.

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

    You can enter your username when prompted, give your username with the
    --myproxy-username option, or set a default myproxy username in config with
    "globus config init" or "globus config set cli.default_myproxy_username".

    For security it is recommended that you only enter your password when
    prompted to hide your inputs and keep your password out of your
    command history, but you may pass your password with the hidden
    --myproxy-password or -P options.""")
@common_options
@endpoint_id_arg
@click.option("--web", is_flag=True, default=False,
              help="Use web activation. Mutually exclusive with --myproxy.")
@click.option("--no-browser", is_flag=True, default=False,
              help=("If using --web, Give a url to manually follow instead of "
                    "opening your default web browser. Implied if on a "
                    "remote session."))
@click.option("--myproxy", is_flag=True, default=False,
              help="Use myproxy activation. Mutually exclusive with --web")
@click.option("--myproxy-username", "-U",
              help=("Give a username to use with --myproxy "
                    "Overrides any default myproxy username set in config."))
@click.option("--myproxy-password", "-P", cls=HiddenOption)
@click.option("--no-autoactivate", is_flag=True, default=False,
              help=("Don't attempt to autoactivate endpoint before using "
                    "--web or --myproxy activation."))
@click.option("--force", is_flag=True, default=False,
              help="Force activation even if endpoint is already activated.")
def endpoint_activate(endpoint_id, myproxy, myproxy_username, myproxy_password,
                      web, no_browser, no_autoactivate, force):
    """
    Executor for `globus endpoint activate`
    """
    default_myproxy_username = lookup_option(MYPROXY_USERNAME_OPTNAME)
    client = get_client()

    # validate options
    if web and myproxy:
        raise click.UsageError("--web is mutually exclusive with --myproxy.")
    if no_autoactivate and not (myproxy or web):
        raise click.UsageError(
            "--no-autoactivate requires --web or --myproxy.")
    if myproxy_username and not myproxy:
        raise click.UsageError("--myproxy-username requires --myproxy.")
    if myproxy_password and not myproxy:
        raise click.UsageError("--myproxy-password requires --myproxy.")
    if no_browser and not web:
        raise click.UsageError("--no-browser requires --web.")

    # check if endpoint is already activated unless --force
    if not force:
        res = client.endpoint_autoactivate(endpoint_id, if_expires_in=60)

        if "AlreadyActivated" == res["code"]:
            OutputFormatter().print_response(res, simple_text=(
                "Endpoint is already activated. Activation "
                "expires at {}".format(res["expire_time"])))
            return

    # attempt autoactivation unless --no-autoactivate
    if not no_autoactivate:

        res = client.endpoint_autoactivate(endpoint_id)

        if "AutoActivated" in res["code"]:
            OutputFormatter().print_response(res, simple_text=(
                "Autoactivation succeeded with message: {}".format(
                    res["message"])))
            return

        # override potentially confusing autoactivation failure response
        else:
            res = {"message": ("Auto-activation failed, please "
                               "use another activation method")}

    # myproxy activation
    if myproxy:

        # get username and password
        if not (myproxy_username or default_myproxy_username):
            myproxy_username = click.prompt("Myproxy username")
        if not myproxy_password:
            myproxy_password = click.prompt(
                "Myproxy password", hide_input=True)

        no_server_msg = ("This endpoint has no myproxy server "
                         "and so cannot be activated through myproxy")

        requirements_data = client.endpoint_get_activation_requirements(
            endpoint_id).data

        if not len(requirements_data["DATA"]):
            raise click.ClickException(no_server_msg)

        for data in requirements_data["DATA"]:
            if data["name"] == "passphrase":
                data["value"] = myproxy_password
            if data["name"] == "username":
                data["value"] = myproxy_username or default_myproxy_username
            if data["name"] == "hostname" and data["value"] is None:
                raise click.ClickException(no_server_msg)

        res = client.endpoint_activate(endpoint_id, requirements_data)

    # web activation
    elif web:
        url = ("https://www.globus.org/app/"
               "endpoints/{}/activate".format(endpoint_id))
        if no_browser or is_remote_session():
            res = {"message": "Web activation url: {}".format(url),
                   "url": url}
        else:
            webbrowser.open(url, new=1)
            res = {"message": "Browser opened to web activation page",
                   "url": url}

    # output
    OutputFormatter(text_format=OutputFormatter.FORMAT_TEXT_RAW,
                    response_key='message').print_response(res)
