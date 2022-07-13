from __future__ import annotations

import os
from typing import Any, Callable, cast

import click

from globus_cli.login_manager import is_client_login, token_storage_adapter
from globus_cli.parsing import command
from globus_cli.termio import FORMAT_TEXT_TABLE, formatted_print
from globus_cli.types import FIELD_LIST_T


def _profilestr_to_datadict(s: str) -> dict[str, Any] | None:
    if s.count("/") < 1:
        return None
    if s.count("/") < 2:
        category, env = s.split("/")
        if category == "clientprofile":  # should not be possible
            return None
        return {"client": False, "env": env, "profile": None, "default": True}
    else:
        category, env, profile = s.split("/", 2)
        return {
            "client": category == "clientprofile",
            "env": env,
            "profile": profile,
            "default": False,
        }


def _parse_and_filter_profiles(
    all: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    globus_env = os.getenv("GLOBUS_SDK_ENVIRONMENT", "production")

    client_profiles = []
    user_profiles = []
    for n in token_storage_adapter().iter_namespaces(include_config_namespaces=True):
        data = _profilestr_to_datadict(n)
        if not data:  # skip any parse failures
            continue
        if (
            data["env"] != globus_env and not all
        ):  # unless --all was passed, skip other envs
            continue
        if data["client"]:
            client_profiles.append(data)
        else:
            user_profiles.append(data)

    return (client_profiles, user_profiles)


def _get_current_checker() -> Callable[[dict[str, Any]], str]:
    is_client = is_client_login()

    def is_current(data: dict[str, Any]) -> bool:
        globus_env = os.getenv("GLOBUS_SDK_ENVIRONMENT", "production")
        if data["env"] != globus_env:
            return False
        if is_client != data["client"]:
            return False
        if data["client"]:
            return cast(str, data["profile"]) == os.getenv("GLOBUS_CLI_CLIENT_ID")
        else:
            return cast(str, data["profile"]) == os.getenv("GLOBUS_PROFILE")

    def field_callback(data: dict[str, Any]) -> str:
        if is_current(data):
            return "-> "
        return ""

    return field_callback


@command(
    "cli-profile-list",
    disable_options=["format", "map_http_status"],
)
@click.option("--all", is_flag=True, hidden=True)
def cli_profile_list(*, all: bool) -> None:
    """
    List all CLI profiles which have been used

    These are the values for GLOBUS_PROFILE which have been recorded, as well as
    GLOBUS_CLI_CLIENT_ID values which have been used.
    """

    client_profiles, user_profiles = _parse_and_filter_profiles(all)
    current_profile_field = _get_current_checker()

    if user_profiles:
        fields: FIELD_LIST_T = [
            ("", current_profile_field),
            ("GLOBUS_PROFILE", "profile"),
            ("is_default", lambda x: "True" if x["default"] else "False"),
        ]
        if all:
            fields += [
                ("GLOBUS_SDK_ENVIRONMENT", "env"),
            ]
        formatted_print(user_profiles, text_format=FORMAT_TEXT_TABLE, fields=fields)
    if client_profiles:
        click.echo("")
        fields = [
            ("", current_profile_field),
            ("GLOBUS_CLI_CLIENT_ID", "profile"),
        ]
        if all:
            fields.append(("GLOBUS_SDK_ENVIRONMENT", "env"))
        formatted_print(client_profiles, text_format=FORMAT_TEXT_TABLE, fields=fields)
