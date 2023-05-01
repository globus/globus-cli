from __future__ import annotations

import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import IdentityType, ParsedIdentity, command
from globus_cli.termio import display


def group_leave_formatter(data: globus_sdk.GlobusHTTPResponse) -> None:
    if "errors" in data:
        click.echo("Encountered errors leaving group, partial success")
        for error_doc in data.get("errors", {}).get("leave", []):
            try:
                click.echo(
                    f"  error: {error_doc['detail']} ({error_doc['identity_id']})"
                )
            except KeyError:
                click.echo("  error: <<no detail>>")
        click.echo()

    values = [f"{x['identity_id']} ({x['username']})" for x in data["leave"]]
    if len(values) == 1:
        click.echo(f"Left group as {values[0]}")
    else:
        click.echo("Left group as")
        for v in values:
            click.echo(f"  {v}")


@command("leave", short_help="Leave a group")
@click.argument("group_id", type=click.UUID)
@click.option(
    "--identity",
    type=IdentityType(),
    help="Only remove membership for a specific identity, not all identities",
)
@LoginManager.requires_login("groups")
def group_leave(
    *,
    group_id: uuid.UUID,
    identity: ParsedIdentity | None,
    login_manager: LoginManager,
) -> None:
    """
    Leave a group in which you are a member.

    If multiple identities in your identity set are members, all memberships will be
    removed by default. If needed, use the `--identity` flag to control this behavior.

    You may not leave a group in which you are the last remaining `admin` user.
    """
    auth_client = login_manager.get_auth_client()
    groups_client = login_manager.get_groups_client()

    if identity:
        identity_id = auth_client.maybe_lookup_identity_id(identity.value)
        if not identity_id:
            raise click.UsageError(
                f"Couldn't determine identity from value: {identity}"
            )
        actions = {"leave": [{"identity_id": identity_id}]}
    else:
        group = groups_client.get_group(group_id, include="my_memberships")
        memberships = [x for x in group["my_memberships"] if x["status"] == "active"]
        if not memberships:
            raise click.ClickException(f"You have no memberships in {group_id}")
        actions = {"leave": [{"identity_id": x["identity_id"]} for x in memberships]}

    response = groups_client.batch_membership_action(group_id, actions)
    # if this failed to return at least one 'leave', figure out an error to show
    if not response.get("leave", None):
        try:
            raise ValueError(response["errors"]["leave"][0]["detail"])
        except LookupError:
            raise ValueError("Could not leave group")

    display(response, text_mode=group_leave_formatter)
