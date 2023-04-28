from __future__ import annotations

import sys

import click
import pytest

from globus_cli.reflect import iter_all_commands
from tests.click_types import check_has_correct_annotations_for_click_args

_SKIP_MODULES = (
    "globus_cli.commands.api",
    "globus_cli.commands.collection.delete",
    "globus_cli.commands.collection.list",
    "globus_cli.commands.collection.show",
    "globus_cli.commands.delete",
    "globus_cli.commands.endpoint.deactivate",
    "globus_cli.commands.endpoint.delete",
    "globus_cli.commands.endpoint.local_id",
    "globus_cli.commands.endpoint.my_shared_endpoint_list",
    "globus_cli.commands.endpoint.permission.create",
    "globus_cli.commands.endpoint.permission.delete",
    "globus_cli.commands.endpoint.permission.list",
    "globus_cli.commands.endpoint.permission.show",
    "globus_cli.commands.endpoint.permission.update",
    "globus_cli.commands.endpoint.role.create",
    "globus_cli.commands.endpoint.search",
    "globus_cli.commands.endpoint.server.add",
    "globus_cli.commands.endpoint.server.delete",
    "globus_cli.commands.endpoint.server.list",
    "globus_cli.commands.endpoint.server.show",
    "globus_cli.commands.endpoint.server.update",
    "globus_cli.commands.endpoint.set_subscription_id",
    "globus_cli.commands.endpoint.show",
    "globus_cli.commands.endpoint.storage_gateway.list",
    "globus_cli.commands.endpoint.user_credential.create.from_json",
    "globus_cli.commands.endpoint.user_credential.create.posix",
    "globus_cli.commands.endpoint.user_credential.create.s3",
    "globus_cli.commands.endpoint.user_credential.delete",
    "globus_cli.commands.endpoint.user_credential.list",
    "globus_cli.commands.endpoint.user_credential.show",
    "globus_cli.commands.endpoint.user_credential.update.from_json",
    "globus_cli.commands.flows.list",
    "globus_cli.commands.flows.start",
    "globus_cli.commands.get_identities",
    "globus_cli.commands.group.create",
    "globus_cli.commands.group.invite.accept",
    "globus_cli.commands.group.invite.decline",
    "globus_cli.commands.group.join",
    "globus_cli.commands.group.leave",
    "globus_cli.commands.group.list",
    "globus_cli.commands.group.member.add",
    "globus_cli.commands.group.member.approve",
    "globus_cli.commands.group.member.invite",
    "globus_cli.commands.group.member.list",
    "globus_cli.commands.group.member.reject",
    "globus_cli.commands.group.member.remove",
    "globus_cli.commands.group.set_policies",
    "globus_cli.commands.group.show",
    "globus_cli.commands.group.update",
    "globus_cli.commands.list_commands",
    "globus_cli.commands.login",
    "globus_cli.commands.logout",
    "globus_cli.commands.ls",
    "globus_cli.commands.mkdir",
    "globus_cli.commands.rename",
    "globus_cli.commands.rm",
    "globus_cli.commands.search.delete_by_query",
    "globus_cli.commands.search.index.role.create",
    "globus_cli.commands.search.ingest",
    "globus_cli.commands.search.query",
)

_ALL_NON_GROUP_COMMANDS: tuple[click.Command, ...] = (
    ctx.command
    for ctx in iter_all_commands(skip_hidden=False)
    if not isinstance(ctx.command, click.Group)
)
_ALL_COMMANDS_TO_TEST: tuple[tuple[str, str], ...] = (
    command
    for command in _ALL_NON_GROUP_COMMANDS
    if command.callback.__module__ not in _SKIP_MODULES
)


def _command_id_fn(val):
    assert isinstance(val, click.Command)
    return val.callback.__module__


@pytest.mark.skipif(sys.version_info < (3, 10), reason="test requires py3.10+")
@pytest.mark.parametrize("command", _ALL_COMMANDS_TO_TEST, ids=_command_id_fn)
def test_annotations_match_click_params(command):
    check_has_correct_annotations_for_click_args(command)
