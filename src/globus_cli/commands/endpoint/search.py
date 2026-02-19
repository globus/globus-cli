from __future__ import annotations

import typing as t

import click
import globus_sdk
from globus_sdk.paging import Paginator

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import OMITTABLE_STRING, OmittableChoice, command
from globus_cli.termio import display
from globus_cli.utils import PagingWrapper


@command(
    "search",
    short_help="Find and discover endpoints.",
    adoc_synopsis="""
`globus endpoint search [OPTIONS] FILTER_FULLTEXT`

`globus endpoint search --filter-scope SCOPE [OPTIONS] [FILTER_FULLTEXT]`
""",
    adoc_examples="""Search for the Globus tutorial endpoints

[source,bash]
----
$ globus endpoint search Tutorial --filter-owner-id go@globusid.org
----

Search for endpoints owned by the current user.

[source,bash]
----
$ globus endpoint search --filter-scope my-endpoints
----
""",
)
@click.option(
    "--filter-scope",
    default="all",
    show_default=True,
    type=click.Choice(
        (
            "all",
            "administered-by-me",
            "my-endpoints",
            "my-gcp-endpoints",
            "recently-used",
            "in-use",
            "shared-by-me",
            "shared-with-me",
        ),
        case_sensitive=False,
    ),
    help="The set of endpoints to search over.",
)
@click.option(
    "--filter-owner-id",
    help=(
        "Filter search results to endpoints owned by a specific "
        "identity. Can be the Identity ID, or the Identity "
        'Username, as in "go@globusid.org"'
    ),
)
@click.option(
    "--limit",
    default=25,
    show_default=True,
    type=click.IntRange(1, 1000),
    help="The maximum number of results to return.",
)
@click.option(
    "--filter-entity-type",
    default=globus_sdk.MISSING,
    type=OmittableChoice(
        (
            "GCP_mapped_collection",
            "GCP_guest_collection",
            "GCSv5_endpoint",
            "GCSv5_mapped_collection",
            "GCSv5_guest_collection",
        ),
        case_sensitive=False,
    ),
    help="Filter search results to endpoints of a specific entity type.",
)
@click.argument(
    "filter_fulltext", required=False, default=globus_sdk.MISSING, type=OMITTABLE_STRING
)
@LoginManager.requires_login("auth", "transfer")
def endpoint_search(
    login_manager: LoginManager,
    *,
    filter_fulltext: str | globus_sdk.MissingType,
    limit: int,
    filter_owner_id: str | None,
    filter_scope: t.Literal[
        "all",
        "administered-by-me",
        "my-endpoints",
        "my-gcp-endpoints",
        "recently-used",
        "in-use",
        "shared-by-me",
        "shared-with-me",
    ],
    filter_entity_type: (
        t.Literal[
            "GCP_mapped_collection",
            "GCP_guest_collection",
            "GCSv5_endpoint",
            "GCSv5_mapped_collection",
            "GCSv5_guest_collection",
        ]
        | globus_sdk.MissingType
    ),
) -> None:
    """
    Search for Globus endpoints with search filters. If --filter-scope is set to the
    default of 'all', then FILTER_FULLTEXT is required.

    If FILTER_FULLTEXT is given, endpoints which have attributes (display name,
    legacy name, description, organization, department, keywords) that match the
    search text will be returned. The result size limit is 100 endpoints.

    If the default table output is too wide for your terminal consider using
    --format record.
    """
    from globus_cli.services.transfer import (
        ENDPOINT_LIST_FIELDS,
        iterable_response_to_dict,
    )

    if filter_scope == "all" and not filter_fulltext:
        raise click.UsageError(
            "When searching all endpoints (--filter-scope=all, the default), "
            "a full-text search filter is required. Other scopes (e.g. "
            "--filter-scope=recently-used) may be used without specifying "
            "an additional filter."
        )

    transfer_client = login_manager.get_transfer_client()
    auth_client = login_manager.get_auth_client()

    owner_id = filter_owner_id
    if owner_id:
        owner_id = auth_client.maybe_lookup_identity_id(owner_id)

    paginator = Paginator.wrap(transfer_client.endpoint_search)
    search_iterator = PagingWrapper(
        paginator(
            filter_fulltext=filter_fulltext,
            filter_scope=filter_scope,
            filter_owner_id=owner_id if owner_id is not None else globus_sdk.MISSING,
            filter_entity_type=filter_entity_type,
        ).items(),
        limit=limit,
    )

    display(
        search_iterator,
        fields=ENDPOINT_LIST_FIELDS,
        json_converter=iterable_response_to_dict,
    )

    if search_iterator.has_next():
        click.echo(
            click.style(
                """
WARNING: More results were available from the Endpoint Search API, but you
         specified a limit lower than the number of available results
""",
                fg="yellow",
            ),
            err=True,
        )
