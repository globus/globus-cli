import click

from globus_cli.parsing import common_options, ENDPOINT_PLUS_REQPATH
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RAW

from globus_cli.services.transfer import get_client, autoactivate


@click.command("symlink", help="Create a symlink on target endpoint")
@common_options
@click.argument("target", metavar="ENDPOINT_ID:TARGET_PATH",
                type=ENDPOINT_PLUS_REQPATH)
@click.argument("link", metavar="ENDPOINT_ID:LINK_PATH",
                type=ENDPOINT_PLUS_REQPATH)
def symlink_command(target, link):
    """
    Executor for `globus symlink`
    """
    target_ep, target_path = target
    link_ep, link_path = link

    if target_ep != link_ep:
        raise click.UsageError(("symlink requires that the target and link "
                                "endpoints are the same, {} != {}")
                               .format(target_ep, link_ep))

    client = get_client()
    autoactivate(client, target_ep, if_expires_in=60)

    res = client.operation_symlink(target_ep, target_path, link_path)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
