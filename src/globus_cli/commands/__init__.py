from globus_cli.commands.bookmark import bookmark_command
from globus_cli.commands.collection import collection_command
from globus_cli.commands.delete import delete_command
from globus_cli.commands.endpoint import endpoint_command
from globus_cli.commands.get_identities import get_identities_command
from globus_cli.commands.group import group_command
from globus_cli.commands.list_commands import list_commands
from globus_cli.commands.login import login_command
from globus_cli.commands.logout import logout_command
from globus_cli.commands.ls import ls_command
from globus_cli.commands.mkdir import mkdir_command
from globus_cli.commands.rename import rename_command
from globus_cli.commands.rm import rm_command
from globus_cli.commands.search import search_command
from globus_cli.commands.session import session_command
from globus_cli.commands.task import task_command
from globus_cli.commands.transfer import transfer_command
from globus_cli.commands.update import update_command
from globus_cli.commands.version import version_command
from globus_cli.commands.whoami import whoami_command
from globus_cli.parsing import main_group


@main_group
def main():
    """
    Interact with Globus from the command line

    All `globus` subcommands support `--help` documentation.

    Use `globus login` to get started!

    The documentation is also online at https://docs.globus.org/cli/
    """


main.add_command(list_commands)
main.add_command(version_command)
main.add_command(update_command)

main.add_command(login_command)
main.add_command(logout_command)
main.add_command(whoami_command)

main.add_command(get_identities_command)
main.add_command(ls_command)
main.add_command(mkdir_command)
main.add_command(rename_command)
main.add_command(delete_command)
main.add_command(rm_command)
main.add_command(transfer_command)

main.add_command(endpoint_command)
main.add_command(collection_command)
main.add_command(bookmark_command)
main.add_command(task_command)
main.add_command(session_command)

main.add_command(group_command)

main.add_command(search_command)
