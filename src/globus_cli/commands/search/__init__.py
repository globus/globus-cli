from globus_cli.parsing import group

from .delete_by_query import delete_by_query_command
from .index import index_command
from .ingest import ingest_command
from .query import query_command
from .task import task_command


@group("search")
def search_command():
    """Use Globus Search to store and query for data"""


search_command.add_command(ingest_command)
search_command.add_command(index_command)
search_command.add_command(query_command)
search_command.add_command(delete_by_query_command)
search_command.add_command(task_command)
