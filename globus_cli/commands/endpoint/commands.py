from globus_cli.parsing import globus_group

from globus_cli.commands.endpoint.permission import permission_command
from globus_cli.commands.endpoint.role import role_command
from globus_cli.commands.endpoint.server import server_command

from globus_cli.commands.endpoint.search import endpoint_search
from globus_cli.commands.endpoint.show import endpoint_show
from globus_cli.commands.endpoint.create import endpoint_create
from globus_cli.commands.endpoint.update import endpoint_update
from globus_cli.commands.endpoint.delete import endpoint_delete
from globus_cli.commands.endpoint.is_activated import endpoint_is_activated
from globus_cli.commands.endpoint.deactivate import endpoint_deactivate
from globus_cli.commands.endpoint.my_shared_endpoint_list import (
    my_shared_endpoint_list)


@globus_group(name='endpoint', help='Manage Globus Endpoint definitions')
def endpoint_command():
    pass


# groups
endpoint_command.add_command(permission_command)
endpoint_command.add_command(role_command)
endpoint_command.add_command(server_command)

# commands
endpoint_command.add_command(endpoint_search)
endpoint_command.add_command(endpoint_show)
endpoint_command.add_command(endpoint_create)
endpoint_command.add_command(endpoint_update)
endpoint_command.add_command(endpoint_delete)

endpoint_command.add_command(endpoint_is_activated)
endpoint_command.add_command(endpoint_deactivate)

endpoint_command.add_command(my_shared_endpoint_list)
