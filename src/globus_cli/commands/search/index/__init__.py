from globus_cli.parsing import group

from .create import create_command
from .delete import delete_command
from .list import list_command
from .role import role_command
from .show import show_command


@group("index")
def index_command():
    """View and manage indices"""


index_command.add_command(create_command)
index_command.add_command(delete_command)
index_command.add_command(list_command)
index_command.add_command(show_command)
index_command.add_command(role_command)
