from __future__ import annotations

import contextlib
import functools
import typing as t
import uuid

import click
import globus_sdk
import globus_sdk.gare
import globus_sdk.scopes

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import OMITTABLE_STRING, JSONStringOrFile
from globus_cli.utils import CLIAuthRequirementsError

_input_schema_helptext = """
        The JSON input schema that governs the parameters
        used to start the flow.

        The input document may be specified inline, or it may be a path to a JSON file.

        Example: Inline JSON:

        \b
            --input-schema '{"properties": {"src": {"type": "string"}}}'

        Example: Path to JSON file:

        \b
            --input-schema schema.json
    """

input_schema_option = click.option(
    "--input-schema",
    "input_schema",
    type=JSONStringOrFile(),
    help=_input_schema_helptext,
)

input_schema_option_with_default = click.option(
    "--input-schema",
    "input_schema",
    type=JSONStringOrFile(),
    help=_input_schema_helptext
    + "\n    If unspecified, the default is an empty JSON object ('{}').",
)

subtitle_option = click.option(
    "--subtitle",
    type=OMITTABLE_STRING,
    help="A concise summary of the flow's purpose.",
    default=globus_sdk.MISSING,
)


description_option = click.option(
    "--description",
    type=OMITTABLE_STRING,
    help="A detailed description of the flow's purpose.",
    default=globus_sdk.MISSING,
)


administrators_option = click.option(
    "--administrator",
    "administrators",
    type=str,
    multiple=True,
    help="""
        A principal that may perform administrative operations
        on the flow (e.g., update, delete).

        This option can be specified multiple times
        to create a list of flow administrators.
    """,
)


starters_option = click.option(
    "--starter",
    "starters",
    type=str,
    multiple=True,
    help="""
        A principal that may start a new run of the flow.

        Use "all_authenticated_users" to allow any authenticated user
        to start a new run of the flow.

        This option can be specified multiple times
        to create a list of flow starters.
    """,
)


viewers_option = click.option(
    "--viewer",
    "viewers",
    type=str,
    multiple=True,
    help="""
        A principal that may view the flow.

        Use "public" to make the flow visible to everyone.

        This option can be specified multiple times
        to create a list of flow viewers.
    """,
)


keywords_option = click.option(
    "--keyword",
    "keywords",
    type=str,
    multiple=True,
    help="""
        A term used to help discover this flow when
        browsing and searching.

        This option can be specified multiple times
        to create a list of keywords.
    """,
)


class SubscriptionIdType(click.ParamType):
    name = "SUBSCRIPTION_ID"

    def __init__(self, *, omittable: bool = False) -> None:
        self._omittable = omittable

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> uuid.UUID | t.Literal["DEFAULT"] | globus_sdk.MissingType:
        if self._omittable and value is globus_sdk.MISSING:
            return globus_sdk.MISSING

        if value.upper() == "DEFAULT":
            return "DEFAULT"
        try:
            return uuid.UUID(value)
        except ValueError:
            self.fail(f"{value} must be either a UUID or 'DEFAULT'", param, ctx)

    def get_type_annotation(self, param: click.Parameter) -> type:
        if self._omittable:
            return t.Union[  # type: ignore[return-value]
                uuid.UUID, t.Literal["DEFAULT"], globus_sdk.MissingType
            ]
        return t.Union[uuid.UUID, t.Literal["DEFAULT"]]  # type: ignore[return-value]


subscription_id_option = click.option(
    "--subscription-id",
    "subscription_id",
    type=SubscriptionIdType(omittable=True),
    multiple=False,
    help="""
        A subscription ID to assign to the flow.

        The value may be a UUID or the word "DEFAULT".
    """,
    default=globus_sdk.MISSING,
)


class FlowScopeInjector:
    """
    A context manager for injecting flow-specific scopes into raised GAREs.

    Usage (flow api):
    >>> with FlowScopeInjector(login_manager).for_flow(flow_id):
    >>>     flows_client.get_flow(flow_id)

    Usage (run api):
    >>> with FlowScopeInjector(login_manager).for_run(run_id):
    >>>     flows_client.get_run(run_id)

    In either case, if the function call raises a GARE-compatible GlobusAPIError,
    the context manager will inject the appropriate flow-specific scope into the
    GARE's required scope section, reraising it as a CLIAuthRequirementsError.

    Using this ensures that the suggested remediation command will update the relevant
    specific-flow's token, not just the statically-registered flows tokens.
    This can resolve issues where a user, for instance, prints out an HA flow, then
    attempts to run it.
    """

    def __init__(self, login_manager: LoginManager) -> None:
        self._login_manager = login_manager

    @contextlib.contextmanager
    def for_flow(self, flow_id: uuid.UUID) -> t.Iterator[None]:
        """
        Context Manager to wrap a flow operation.

        If the wrapped operation raises a GARE, this manager will re-raise it
        with the flow-specific scope injected.
        """
        try:
            yield
        except globus_sdk.GlobusAPIError as api_error:
            self._inject_and_raise(api_error, lambda: flow_id)

    @contextlib.contextmanager
    def for_run(self, run_id: uuid.UUID) -> t.Iterator[None]:
        """
        Context manager to wrap a flow run operation.

        If the wrapped operation raises a GARE, this manager will attempt to look up
        the associated flow ID from search & re-raise it with the flow-specific scope.

        If the lookup fails, the original error is raised unmodified.
        """
        try:
            yield
        except globus_sdk.GlobusAPIError as api_error:
            resolver = FlowIdResolver(self._login_manager)
            resolve_flow_id = functools.partial(resolver.resolve, run_id)

            self._inject_and_raise(api_error, resolve_flow_id)

    @staticmethod
    def _inject_and_raise(
        api_error: globus_sdk.GlobusAPIError,
        resolve_flow_id: t.Callable[[], uuid.UUID | None],
    ) -> None:
        """
        :raises GlobusAPIError: if the supplied api error is not GARE-compatible
        :raises CLIAuthRequirementsError: otherwise with the flow-scope injected into
            the required scopes (assuming it wasn't already there).
        """
        if (gare := globus_sdk.gare.to_gare(api_error)) is None or (
            (flow_id := resolve_flow_id()) is None
        ):
            raise api_error

        flow_scope = globus_sdk.scopes.SpecificFlowScopes(flow_id).user.scope_string

        required_scopes = gare.authorization_parameters.required_scopes or []
        # Make sure that no root scopes match the one we want to inject.
        if not any(s.startswith(flow_scope) for s in required_scopes):
            required_scopes.insert(0, flow_scope)
        gare.authorization_parameters.required_scopes = required_scopes

        raise CLIAuthRequirementsError("", gare=gare)


class FlowIdResolver:
    RUN_INDEX = "2a318659-a547-4b48-a0fc-e0c19081a960"

    def __init__(self, login_manager: LoginManager) -> None:
        self._search_client = login_manager.get_search_client()

    def resolve(self, run_id: uuid.UUID) -> uuid.UUID | None:
        """
        Lookup a run's associated flow ID from search (best-effort).

        :return: The flow ID as a UUID, or None if the lookup fails or is unparsable
            for any reason.
        """

        try:
            flow_id = self._search_client.post_search(
                self.RUN_INDEX,
                {
                    "filters": [
                        {
                            "type": "match_any",
                            "field_name": "run_id",
                            "values": [str(run_id)],
                        }
                    ],
                    "limit": 1,
                },
            )["gmeta"][0]["entries"][0]["content"]["flow_id"]
            return uuid.UUID(flow_id)
        except (globus_sdk.GlobusError, LookupError):
            # This search is a best-effort flows-operation.
            # To avoid mis-categorizing a flows error as a search one, silence any
            #   predictable error arising from a failed lookup.
            return None
