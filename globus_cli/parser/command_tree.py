import textwrap

from globus_cli.helpers import cliargs
from globus_cli.parser.shared_parser import GlobusCLISharedParser
from globus_cli.parser.helpers import (
    not_implemented_func, FuncCommand, MenuCommand, add_cli_args)
from globus_cli.services import auth, transfer


@cliargs('Show login help', [])
def login_help(args):
    print('\nTo login to the Globus CLI, go to\n')
    print('    https://tokens.globus.org/\n')
    print('and follow the instructions for the Globus CLI\n')


@cliargs('Show simplified help text for all Globus CLI commands', [])
def full_help_func(args, tree=None, parent_name='globus'):
    """
    Print long-form help for all commands. Must go in this module to have
    _COMMAND_TREE in scope.
    """
    # cap a line at 78 chars
    _max_len = 78

    def cmd_fullname(cmd, noglobus=False):
        if noglobus:
            prefix = parent_name[7:]
        else:
            prefix = parent_name

        if prefix:
            prefix = prefix + ' '

        return prefix + cmd.name

    def help_text(cmd, helpindent=0):
        # wrap lines of help text to have the desired indent, but also fit
        # (with that indent) under the max len for a line
        help_body = textwrap.wrap(cmd.helptext, width=(_max_len - helpindent))
        help_body = '\n'.join(' '*helpindent + l for l in help_body)

        return help_body

    def format_func_cmd(func_cmd):
        start = '\n' + ' '*4 + cmd_fullname(func_cmd) + '\n'

        return start + help_text(func_cmd, helpindent=8)

    def format_menu_cmd(menu_cmd):
        start = ('\n\n== ' +
                 cmd_fullname(menu_cmd, noglobus=True).upper() +
                 ' ==\n')

        return start + help_text(menu_cmd)

    printme = False
    if tree is None:
        headerline = 'Globus CLI Commands'
        print('\n' + headerline)
        print('='*len(headerline))
        printme = True
        tree = _COMMAND_TREE

    funccmd_help = ''
    menucmd_help = ''
    for cmd in tree:
        if isinstance(cmd, FuncCommand):
            funccmd_help += format_func_cmd(cmd) + '\n'
        else:
            menucmd_help += format_menu_cmd(cmd) + '\n'
            menucmd_help += full_help_func(
                args, tree=cmd.commandset, parent_name=cmd_fullname(cmd)
                )

    if funccmd_help and menucmd_help:
        full_help = funccmd_help + menucmd_help
    else:
        full_help = funccmd_help or menucmd_help

    if printme:
        print(full_help)

    return full_help


_AUTH_COMMANDS = [
    FuncCommand('get-identities', auth.get_identities),
    FuncCommand('token-introspect', auth.token_introspect)
]

_TRANSFER_COMMANDS = [
    MenuCommand(
        'endpoint',
        [FuncCommand('show', transfer.endpoint_show),
         FuncCommand('update', not_implemented_func),
         FuncCommand('create', not_implemented_func),
         FuncCommand('search', transfer.endpoint_search),
         FuncCommand('autoactivate', transfer.endpoint_autoactivate),
         FuncCommand('deactivate', transfer.endpoint_deactivate),
         FuncCommand('server-list', transfer.endpoint_server_list),
         FuncCommand('my-shared-endpoint-list',
                     transfer.my_shared_endpoint_list),
         MenuCommand(
            'role',
            [FuncCommand('list', transfer.endpoint_role_list),
             FuncCommand('show', transfer.endpoint_role_show),
             FuncCommand('create', transfer.endpoint_role_create),
             FuncCommand('delete', transfer.endpoint_role_delete)],
            'Manage endpoint roles')
         ],
        'Manage Globus Endpoint definitions'),

    MenuCommand(
        'task',
        [FuncCommand('list', transfer.task_list),
         FuncCommand('event-list', transfer.task_event_list),
         FuncCommand('pause-info', transfer.task_pause_info),
         FuncCommand('cancel', transfer.cancel_task),
         FuncCommand('update', transfer.update_task),
         FuncCommand('show', transfer.show_task)],
        'Manage asynchronous Tasks'),

    MenuCommand(
        'acl',
        [FuncCommand('list', transfer.acl_list),
         FuncCommand('show-rule', transfer.show_acl_rule),
         FuncCommand('add-rule', transfer.add_acl_rule),
         FuncCommand('del-rule', transfer.del_acl_rule),
         FuncCommand('update-rule', transfer.update_acl_rule)],
        'Manage Endpoint Access Control Lists'),

    MenuCommand(
        'bookmark',
        [FuncCommand('list', transfer.bookmark_list),
         FuncCommand('show', transfer.bookmark_show),
         FuncCommand('create', transfer.bookmark_create),
         FuncCommand('rename', transfer.bookmark_rename),
         FuncCommand('delete', transfer.bookmark_delete)],
        'Manage Endpoint Bookmarks'),

    FuncCommand('async-transfer', transfer.submit_transfer),
    FuncCommand('async-delete', transfer.submit_delete),
    FuncCommand('ls', transfer.op_ls),
    FuncCommand('mkdir', transfer.op_mkdir),
    FuncCommand('rename', transfer.op_rename)
]

_COMMAND_TREE = [
    FuncCommand('help', full_help_func),
    FuncCommand('login', login_help),

    MenuCommand('auth', _AUTH_COMMANDS, (
                'Interact with Globus Auth API. '
                'Inspect Tokens, Identities, and Identity Sets, '
                'consent to service terms, revoke and manage Consents, '
                'and manage OAuth Clients')),
    MenuCommand('transfer', _TRANSFER_COMMANDS, (
                'Interact with Globus Transfer API. '
                'Transfer, Delete, List, and Rename files on Endpoints, '
                'manage your Endpoints and Shares, and monitor your ongoing '
                'Transfer Tasks.'))
]


def _add_subcommands(parser, commandset):
    """
    Build out subcommands recursively with this helper method.
    Any given command may have subcommands, ad infinitum, so the simplest
    solution is the recursive one.
    Walk commands, plugging in any that terminate the command tree at a
    function. Any others are menu commands that have further subcommands, and
    those therefore require that we add whatever subcommands they have
    (recursive case).
    """

    # we start with a subparser collection named "Commands"
    subparsers = parser.add_subparsers(
        title='Commands', parser_class=GlobusCLISharedParser,
        metavar='')

    # iterate over all commands in the set, and ...
    for command in commandset:
        current_parser = subparsers.add_parser(
            command.name, help=command.helptext, description=command.helptext)

        # the command wraps a function, build it out
        if isinstance(command, FuncCommand):
            # round up the arguments dangling off of the command and put them
            # in here
            current_parser.set_defaults(func=command.func)
            add_cli_args(current_parser, command.func.cli_arguments)

        # it's a menu, recurse
        else:
            _add_subcommands(current_parser, command.commandset)


def build_command_tree():
    """
    Create a parser from the command tree.
    Add nexus, auth, and transfer subcommands, their subsubcommands, and
    arguments.
    """
    # TODO: Update this description to be more informative, accurate
    description = textwrap.dedent("""Run a globus command.
    The globus command is structured to provide a uniform command line
    interface to all Globus services. For more information and tutorials,
    see docs.globus.org
    """)

    top_level_parser = GlobusCLISharedParser(description=description)
    _add_subcommands(top_level_parser, _COMMAND_TREE)

    # return the created parser in all of its glory
    return top_level_parser
