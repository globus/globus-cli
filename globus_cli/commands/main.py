from globus_cli.parsing import globus_main_func

from globus_cli.commands.list_commands import list_commands
from globus_cli.commands.version import version_command
from globus_cli.commands.update import update_command
from globus_cli.commands.config import config_command

from globus_cli.commands.login import login_command
from globus_cli.commands.logout import logout_command
from globus_cli.commands.whoami import whoami_command

from globus_cli.commands.get_identities import get_identities_command
from globus_cli.commands.ls import ls_command
from globus_cli.commands.delete import delete_command
from globus_cli.commands.transfer import transfer_command
from globus_cli.commands.mkdir import mkdir_command
from globus_cli.commands.rename import rename_command
from globus_cli.commands.symlink import symlink_command

from globus_cli.commands.endpoint import endpoint_command
from globus_cli.commands.bookmark import bookmark_command
from globus_cli.commands.task import task_command


@globus_main_func
def main():
    pass


main.add_command(list_commands)
main.add_command(version_command)
main.add_command(update_command)
main.add_command(config_command)

main.add_command(login_command)
main.add_command(logout_command)
main.add_command(whoami_command)

main.add_command(get_identities_command)
main.add_command(ls_command)
main.add_command(mkdir_command)
main.add_command(rename_command)
main.add_command(delete_command)
main.add_command(transfer_command)
main.add_command(symlink_command)

main.add_command(endpoint_command)
main.add_command(bookmark_command)
main.add_command(task_command)
