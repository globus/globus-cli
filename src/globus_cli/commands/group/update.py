import typing as t

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display

from ._common import group_create_and_update_params, group_id_arg


@group_create_and_update_params()
@group_id_arg
@command("update")
@LoginManager.requires_login("groups")
def group_update(*, login_manager: LoginManager, group_id: str, **kwargs: t.Any):
    """Update an existing group."""
    groups_client = login_manager.get_groups_client()

    # get the current state of the group
    group = groups_client.get_group(group_id)

    # assemble put data using existing values for any field not given
    # note that the API does not accept the full group document, so we must
    # specify name and description instead of just iterating kwargs
    data = {}
    for field in ["name", "description"]:
        if kwargs.get(field) is not None:
            data[field] = kwargs[field]
        else:
            data[field] = group[field]

    response = groups_client.update_group(group_id, data)

    display(response, simple_text="Group updated successfully")
