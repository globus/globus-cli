from __future__ import annotations

import typing as t

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import ENDPOINT_PLUS_OPTPATH, command
from globus_cli.termio import Field, display, formatters, is_verbose, outformat_is_text


class PathItemFormatter(formatters.StrFormatter):
    def parse(self, data: t.Any) -> str:
        if not isinstance(data, dict):
            raise ValueError("cannot parse path item which is not a dict")
        return str(data["name"]) + ("/" if data["type"] == "dir" else "")


@command(
    "ls",
    short_help="List endpoint directory contents",
    adoc_examples=r"""List files and dirs in your default directory on an endpoint

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus ls $ep_id
----

List files and dirs on a specific path on an endpoint

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus ls $ep_id:/share/godata/
----

Do a *globus ls* requesting JSON formatted output

[source,bash]
----
$ globus ls $ep_id:/share/godata/ --format=JSON
----

Take specific fields from the JSON output and format them into unix-friendly
columnar output using '--jmespath' to query and '--format UNIX' to format
output:

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$  globus ls $ep_id:/share/godata/ \
    --jmespath 'DATA[*].[type, permissions, name, last_modified]' \
    --format UNIX
----

=== Filtering

List files and dirs on a specific path on an endpoint, filtering in various
ways.

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus ls $ep_id:/share/godata/ --filter '~*.txt'  # all txt files
$ globus ls $ep_id:/share/godata/ --filter '!~file1.*'  # not starting in "file1."
$ globus ls $ep_id:/share/godata/ --filter '~*ile3.tx*'  # anything with "ile3.tx"
$ globus ls $ep_id:/share/godata/ --filter '=file2.txt'  # only "file2.txt"
$ globus ls $ep_id:/share/godata/ --filter 'file2.txt'  # same as '=file2.txt'
$ globus ls $ep_id:/share/godata/ --filter '!=file2.txt'  # anything but "file2.txt"
----

Compare a grep with a *globus ls --filter*. These two are the same, but the
filter will be faster because it doesn't require that filenames which are
filtered out are returned to the CLI:

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus ls $ep_id:/share/godata/ | egrep '.*\.txt$'  # done with grep, okay
$ globus ls $ep_id:/share/godata/ --filter '~*.txt'  # done with --filter, better
----
""",
)
@click.argument("endpoint_plus_path", type=ENDPOINT_PLUS_OPTPATH)
@click.option(
    "--all",
    "-a",
    "show_hidden",
    is_flag=True,
    help="Show files and directories that start with `.`",
)
@click.option(
    "--long",
    "-l",
    "long_output",
    is_flag=True,
    help="For text output only. Do long form output, kind of like `ls -l`",
)
@click.option(
    "--filter",
    "filter_val",
    metavar="FILTER_PATTERN",
    help="Filter results to filenames matching the given pattern.",
)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    show_default=True,
    help="Do a recursive listing, up to the depth limit. Similar to `ls -R`",
)
@click.option(
    "--recursive-depth-limit",
    default=3,
    show_default=True,
    type=click.IntRange(min=0),
    metavar="INTEGER",
    help=(
        "Limit to number of directories to traverse in "
        "`--recursive` listings. A value of 0 indicates that "
        "this should behave like a non-recursive `ls`"
    ),
)
@LoginManager.requires_login("transfer")
def ls_command(
    *,
    login_manager: LoginManager,
    endpoint_plus_path,
    recursive_depth_limit,
    recursive,
    long_output,
    show_hidden,
    filter_val,
):
    """
    List the contents of a directory on an endpoint. If no path is given, the default
    directory on that endpoint will be used.

    If using text output files and directories are printed with one entry per line in
    alphabetical order.  Directories are always displayed with a trailing '/'.


    \b
    === Filtering

    --filter takes "filter patterns" subject to the following rules.

    \b
    Filter patterns must start with "=", "~", "!", or "!~"
    If none of these are given, "=" will be used

    \b
    "=" does exact matching
    "~" does regex matching, supporting globs (*)
    "!" does inverse "=" matching
    "!~" does inverse "~" matching

    \b
    "~*.txt" matches all .txt files, for example

    {AUTOMATIC_ACTIVATION}
    """
    from globus_sdk.services.transfer.response import IterableTransferResponse

    from globus_cli.services.transfer import (
        RecursiveLsResponse,
        autoactivate,
        iterable_response_to_dict,
    )

    endpoint_id, path = endpoint_plus_path

    # do autoactivation before the `ls` call so that recursive invocations
    # won't do this repeatedly, and won't have to instantiate new clients
    transfer_client = login_manager.get_transfer_client()
    autoactivate(transfer_client, endpoint_id, if_expires_in=60)

    # create the query paramaters to send to operation_ls
    ls_params: dict[str, t.Any] = {"show_hidden": int(show_hidden)}
    if path:
        ls_params["path"] = path

    # this char has special meaning in the LS API's filter clause
    # can't be part of the pattern (but we don't support globbing across
    # dir structures anyway)
    if filter_val and "/" in filter_val:
        raise click.UsageError('--filter cannot contain "/"')

    # get the `ls` result
    if recursive:
        # if we are doing filtering we need to pass multiple filter params. The
        # first allows all directories, as we need them for recursive
        # expansion. The second then filters name by the filter_val
        if filter_val:
            ls_params["filter"] = [{"type": "dir"}, {"name": filter_val}]

        res: (
            IterableTransferResponse | RecursiveLsResponse
        ) = transfer_client.recursive_operation_ls(
            endpoint_id, ls_params, depth=recursive_depth_limit
        )
    else:
        # format filter_val into a simple filter clause which operates on name
        if filter_val:
            ls_params["filter"] = f"name:{filter_val}"

        res = transfer_client.operation_ls(endpoint_id, **ls_params)

    # and then print it, per formatting rules
    pathformatter = PathItemFormatter()
    display(
        res,
        fields=[
            Field("Permissions", "permissions"),
            Field("User", "user"),
            Field("Group", "group"),
            Field("Size", "size"),
            Field("Last Modified", "last_modified"),
            Field("File Type", "type"),
            Field("Filename", "@", formatter=pathformatter),
        ],
        simple_text=(
            None
            if long_output or is_verbose() or not outformat_is_text()
            else "\n".join(pathformatter.parse(x) for x in res)
        ),
        json_converter=iterable_response_to_dict,
    )
