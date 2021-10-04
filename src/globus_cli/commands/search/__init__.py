from globus_cli.commands.search.query import query_command
from globus_cli.parsing import group


@group("search")
def search_command():
    """Use Globus Search to store and query for data"""


search_command.add_command(query_command)
