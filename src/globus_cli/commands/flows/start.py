from __future__ import annotations

import os
import string
import typing as t
import uuid

import click
import globus_sdk

from globus_cli._click_compat import shim_get_metavar
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    JSONStringOrFile,
    ParsedJSONData,
    command,
    flow_id_arg,
    flow_input_document_option,
    OMITTABLE_STRING,
)
from globus_cli.termio import Field, display, formatters
from globus_cli.types import JsonValue

if t.TYPE_CHECKING:
    from click.shell_completion import CompletionItem

ROLE_TYPES = ("flow_viewer", "flow_starter", "flow_administrator", "flow_owner")


class ActivityNotificationPolicyType(JSONStringOrFile):
    """
    An ActivityNotificationPolicy, parsed on the CLI is
    - a comma-delimited list of choices
    OR
    - a JSON filename
    OR
    - a JSON string

    NB: because this inherits JSONStringOrFile, it also accepts `file:<path>` syntax.
    """

    choices = ("INACTIVE", "FAILED", "SUCCEEDED")

    @shim_get_metavar
    def get_metavar(self, param: click.Parameter, ctx: click.Context) -> str:
        return f"[{{{','.join(self.choices)}}}|JSON_FILE|JSON]"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> ParsedJSONData:
        if self._is_nonfile_comma_delimited_str(value):
            return self._parse_comma_delimited(value, param, ctx)
        # the super().convert() return type needs to be ignored because
        # it is annotated as 'ExplicitNullType|ParsedJSONData' but the null case is
        # not reachable because we haven't set a null value
        return super().convert(value, param, ctx)  # type: ignore[return-value]

    def _is_nonfile_comma_delimited_str(self, value: str) -> bool:
        """Determine if an input is a comma-delimited list of values.
        Furthermore, require it to not be a valid filename.

        The heuristic used is
        - split on commas
        - are all of the elements of that split alphanumeric strings

        Anything else gets passed to JSON parsing.
        """
        # real filename or stdin
        if os.path.exists(value) or value == "-":
            return False

        alphabet = set(string.ascii_letters + string.digits)
        return all(set(x) < alphabet for x in value.split(","))

    def _parse_comma_delimited(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> ParsedJSONData:
        """
        Parse comma-delimited choice input (case insensitive) and return the
        result in the form of a ParsedJSONData object with no filename,
        containing the appropriate policy document.
        """
        # empty string -> [], not [""]
        parts = value.split(",") if value else []
        # strip out empty strings, which makes for smooth handling of
        # inputs like "FAILED,INACTIVE," (trailing comma)
        parts = [p for p in parts if p != ""]

        invalid_choices = [p for p in parts if p.upper() not in self.choices]
        if invalid_choices:
            if len(invalid_choices) == 1:
                self.fail(f"{invalid_choices[0]!r} was not a valid choice.", param, ctx)
            else:
                self.fail(f"{invalid_choices!r} were not valid choices.", param, ctx)

        data: JsonValue = {"status": [p.upper() for p in parts]}
        return ParsedJSONData(None, data)

    def shell_complete(
        self, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> list[CompletionItem]:
        from click.shell_completion import CompletionItem

        # if the caller used `--activity-notification-policy <TAB>`, show all options
        # from the list
        if incomplete == "":
            return [CompletionItem(c) for c in self.choices]

        # if the string looks like a comma-delimited string, and doesn't match
        # a filename then completion should treat it as a comma-delimited
        # string
        if self._is_nonfile_comma_delimited_str(incomplete):
            # no comma? could be the start of the first string
            # e.g., `--activity-notification-policy inac<TAB>` ('inac' -> 'INACTIVE')
            #
            # commas? split them, grab the last element, and try working with that
            # e.g., `--activity-notification-policy FAILED,INAC<TAB>`
            #       (FAILED,INAC -> FAILED,INACTIVE)
            #
            # these are actually the same case -- split on commas, get the last
            # string, and use that for completion
            split = incomplete.split(",")
            rightmost = split[-1]

            # before we complete, figure out which choices are already completed
            # we want 'FAILED,' -> FAILED,{INACTIVE|SUCCEEDED}
            # not 'FAILED,' -> FAILED,{FAILED|INACTIVE|SUCCEEDED}
            already_seen_choices = [
                c
                for c in self.choices
                if any(c.startswith(part.upper()) for part in split[:-1])
            ]
            unseen_choices = [c for c in self.choices if c not in already_seen_choices]

            return [
                CompletionItem(",".join(split[:-1] + [c]))
                for c in unseen_choices
                if c.startswith(rightmost.upper())
            ]

        # it didn't look like a comma-separated string?
        # then presumably it's JSON or a filename
        # complete as a filename (which means no completion on JSON strings)
        return [CompletionItem(incomplete, type="file")]


@command("start", short_help="Start a flow.")
@flow_id_arg
@flow_input_document_option
@click.option(
    "--label",
    help="A label to give the run.",
    default=globus_sdk.MISSING,
    type=OMITTABLE_STRING,
)
@click.option(
    "--manager",
    "managers",
    type=str,
    multiple=True,
    help="""
        A principal that may manage the execution of the run.

        This option can be specified multiple times
        to create a list of run managers.
    """,
)
@click.option(
    "--monitor",
    "monitors",
    type=str,
    multiple=True,
    help="""
        A principal that may monitor the execution of the run.

        This option can be specified multiple time
        to create a list of run monitors.
    """,
)
@click.option(
    "--tag",
    "tags",
    type=str,
    multiple=True,
    help="""
        A tag to associate with the run.

        This option can be used multiple times
        to create a list of tags.
    """,
)
@click.option(
    "--activity-notification-policy",
    type=ActivityNotificationPolicyType(),
    help="""
        The activity notification policy for the run.

        This may be given as a comma-delimited list of statuses for notification;
        alternatively, this can also be provided as JSON data--or a path to a
        JSON file--containing a full notification policy document.
    """,
)
@LoginManager.requires_login("flows")
def start_command(
    login_manager: LoginManager,
    *,
    flow_id: uuid.UUID,
    input_document: ParsedJSONData | None,
    label: str | globus_sdk.MissingType,
    managers: tuple[str, ...],
    monitors: tuple[str, ...],
    tags: tuple[str, ...],
    activity_notification_policy: ParsedJSONData | None,
) -> None:
    """
    Start a flow.

    This creates a new run, and will return the run ID for monitoring and
    future interactions with that run of the flow.
    The input data will be validated against the Flow's input schema if one is
    declared.

    Use tags and labels to make runs searchable, and set monitors and managers
    to allow other users to interact with the run.

    The notification policy defaults to `"INACTIVE"`. You can set it to the full
    set of statuses, as in

    \b
    --activity-notification-policy 'INACTIVE,SUCCEEDED,FAILED'

    Or pass a full notification policy document as JSON.
    """

    if input_document is None:
        input_document_json: dict[str, JsonValue] = {}
    else:
        if not isinstance(input_document.data, dict):
            raise click.UsageError("Flow input must be a JSON object")
        input_document_json = input_document.data

    notify_policy: dict[str, t.Any] | globus_sdk.MissingType = globus_sdk.MISSING
    if activity_notification_policy:
        if not isinstance(activity_notification_policy.data, dict):
            raise click.UsageError(
                "Activity Notification Policy must be a JSON object."
            )
        notify_policy = activity_notification_policy.data

    flow_client = login_manager.get_specific_flow_client(flow_id)
    response = flow_client.run_flow(
        body=input_document_json,
        label=label,
        tags=list(tags),
        run_managers=list(managers),
        run_monitors=list(monitors),
        activity_notification_policy=notify_policy,
    )

    auth_client = login_manager.get_auth_client()
    principal_formatter = formatters.auth.PrincipalURNFormatter(auth_client)
    for principal_set_name in ("run_managers", "run_monitors"):
        for value in response.get(principal_set_name, ()):
            principal_formatter.add_item(value)
    principal_formatter.add_item(response.get("run_owner"))

    fields = [
        Field("Flow ID", "flow_id"),
        Field("Flow title", "flow_title"),
        Field("Run ID", "run_id"),
        Field("Run label", "label"),
        Field(
            "Run owner",
            "run_owner",
            formatter=principal_formatter,
        ),
        Field(
            "Run managers",
            "run_managers",
            formatter=formatters.ArrayFormatter(
                delimiter=", ",
                element_formatter=principal_formatter,
            ),
        ),
        Field(
            "Run monitors",
            "run_monitors",
            formatter=formatters.ArrayFormatter(
                delimiter=", ",
                element_formatter=principal_formatter,
            ),
        ),
        Field(
            "Run tags",
            "tags",
            formatter=formatters.ArrayFormatter(delimiter=", "),
        ),
    ]

    display(response, fields=fields, text_mode=display.RECORD)
