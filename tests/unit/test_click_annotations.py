import importlib
import sys

import pytest

from tests.click_types import check_has_correct_annotations_for_click_args


@pytest.mark.skipif(sys.version_info < (3, 10), reason="test requires py3.10+")
@pytest.mark.parametrize(
    "modname, command_name",
    (
        ("cli_profile_list", "cli_profile_list"),
        ("transfer", "transfer_command"),
        ("update", "update_command"),
        ("version", "version_command"),
        ("whoami", "whoami_command"),
    ),
)
def test_annotations_match_click_params(modname, command_name):
    mod = importlib.import_module(f"globus_cli.commands.{modname}", "globus_cli")
    cmd = getattr(mod, command_name)

    check_has_correct_annotations_for_click_args(cmd)
