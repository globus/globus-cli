import importlib
import sys

import pytest

from tests.click_types import check_has_correct_annotations_for_click_args


@pytest.mark.skipif(sys.version_info < (3, 10), reason="test requires py3.10+")
@pytest.mark.parametrize(
    "modname, command_name",
    (
        ("bookmark.create", "bookmark_create"),
        ("bookmark.delete", "bookmark_delete"),
        ("bookmark.list", "bookmark_list"),
        ("bookmark.rename", "bookmark_rename"),
        ("bookmark.show", "bookmark_show"),
        ("cli_profile_list", "cli_profile_list"),
        ("collection.update", "collection_update"),
        ("endpoint.create", "endpoint_create"),
        ("endpoint.is_activated", "endpoint_is_activated"),
        # TODO: role_create uses the security_principal_opts decorator, which transforms
        # arguments. This needs to be refactored to be checkable using this method
        # ("endpoint.role.create", "role_create"),
        ("endpoint.role.delete", "role_delete"),
        ("endpoint.role.list", "role_list"),
        ("endpoint.role.show", "role_show"),
        ("endpoint.update", "endpoint_update"),
        ("gcp.create.guest", "guest_command"),
        ("gcp.create.mapped", "mapped_command"),
        ("session.update", "session_update"),
        ("transfer", "transfer_command"),
        ("timer.delete", "delete_command"),
        ("timer.list", "list_command"),
        ("timer.show", "show_command"),
        ("timer.create.transfer", "transfer_command"),
        ("update", "update_command"),
        ("version", "version_command"),
        ("whoami", "whoami_command"),
    ),
)
def test_annotations_match_click_params(modname, command_name):
    mod = importlib.import_module(f"globus_cli.commands.{modname}", "globus_cli")
    cmd = getattr(mod, command_name)

    check_has_correct_annotations_for_click_args(cmd)
