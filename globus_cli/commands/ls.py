import click

from globus_cli.parsing import common_options, ENDPOINT_PLUS_OPTPATH
from globus_cli.safeio import formatted_print
from globus_cli.helpers import is_verbose, outformat_is_json
from globus_cli.services.transfer import (
    get_client, autoactivate, iterable_response_to_dict)


@click.command('ls', help='List the contents of a directory on an endpoint',
               short_help='List endpoint directory contents')
@common_options
@click.argument('endpoint_plus_path', metavar=ENDPOINT_PLUS_OPTPATH.metavar,
                type=ENDPOINT_PLUS_OPTPATH)
@click.option('--all', '-a', is_flag=True,
              help=('Show files and directories that start with `.`'))
@click.option('--long', '-l', is_flag=True,
              help=('For text output only. Do long form output, kind '
                    'of like `ls -l`'))
@click.option('--recursive', '-r', is_flag=True, show_default=True,
              help=('Do a recursive listing, up to the depth limit. '
                    'Similar to `ls -R`'))
@click.option('--recursive-depth-limit', default=3, show_default=True,
              type=click.IntRange(min=0), metavar='INTEGER',
              help=('Limit to number of directories to traverse in '
                    '`--recursive` listings. A value of 0 indicates that '
                    'this should behave like a non-recursive `ls`'))
@click.option("--follow-symlinks", is_flag=True, show_default=True,
              help="Follow directory symlinks during recursive listings.")
def ls_command(endpoint_plus_path, recursive_depth_limit,
               recursive, long, all, follow_symlinks):
    """
    Executor for `globus ls`
    """
    # validate options
    if follow_symlinks and not recursive:
        raise click.UsageError(("Cannot --follow-symlinks during "
                                "non --recursive listings"))

    endpoint_id, path = endpoint_plus_path

    # do autoactivation before the `ls` call so that recursive invocations
    # won't do this repeatedly, and won't have to instantiate new clients
    client = get_client()
    autoactivate(client, endpoint_id, if_expires_in=60)

    # create the query paramaters to send to operation_ls
    ls_params = {"show_hidden": int(all)}
    if path:
        ls_params["path"] = path

    # get the `ls` result
    if recursive:
        res = client.recursive_operation_ls(
            endpoint_id, depth=recursive_depth_limit,
            follow_symlinks=follow_symlinks, **ls_params)
    else:
        res = client.operation_ls(endpoint_id, **ls_params)

    def long_item_name(item):
        if item["link_target"]:
            return cleaned_item_name(item) + " -> " + item["link_target"]
        else:
            return cleaned_item_name(item)

    def long_item_type(item):
        if item["link_target"] and item["type"] != "invalid_symlink":
            return item["type"] + " (symlink)"
        else:
            return item["type"]

    def cleaned_item_name(item):
        return item['name'] + ('/' if item['type'] == 'dir' else '')

    # and then print it, per formatting rules
    formatted_print(
        res, fields=[('Permissions', 'permissions'), ('User', 'user'),
                     ('Group', 'group'), ('Size', 'size'),
                     ('Last Modified', 'last_modified'),
                     ('File Type', long_item_type),
                     ('Filename', long_item_name)],
        simple_text=(None if long or is_verbose() or outformat_is_json() else
                     "\n".join(cleaned_item_name(x) for x in res)),
        json_converter=iterable_response_to_dict)
