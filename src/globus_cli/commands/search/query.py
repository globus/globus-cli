import json
from io import TextIOWrapper
from typing import Any, Dict, List, Optional

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import CommaDelimitedList, command, mutex_option_group
from globus_cli.services.search import get_search_client
from globus_cli.termio import FORMAT_TEXT_RAW, formatted_print


@command("query", short_help="Perform a search")
@click.option("-q", help="The query-string to use to search the index.")
@click.option(
    "--query-document",
    type=click.File("r"),
    help="A complete query document to use to search the index.",
)
@click.option("--limit", type=int, help="Limit the number of results to return")
@click.option(
    "--advanced",
    is_flag=True,
    help="Perform the search using the advanced query syntax",
)
@click.option(
    "--bypass-visible-to",
    is_flag=True,
    help="Bypass the visible_to restriction on searches. "
    "This option is only available to the admins of an index",
)
@click.option(
    "--filter-principal-sets",
    type=CommaDelimitedList(),
    help=(
        "A principal-sets filter to apply to the results, allowing filtering by "
        "predefined sets of identities or groups. Supplied as a comma-delimited list."
    ),
)
@click.argument("INDEX_ID")
@mutex_option_group("-q", "--query-document")
@LoginManager.requires_login(LoginManager.SEARCH_RS)
def query_command(
    index_id: str,
    q: Optional[str],
    query_document: Optional[TextIOWrapper],
    limit: Optional[int],
    advanced: bool,
    bypass_visible_to: bool,
    filter_principal_sets: Optional[List[str]],
):
    """
    Query a Globus Search Index by ID using either a simple query string, or a complex
    query document. At least one of `-q` or `--query-document` must be provided.

    If a query document and command-line options are provided, the options used will
    override any options which were present on the query document.
    """
    search_client = get_search_client()

    if q:
        query_params: Dict[str, Any] = {}
        if filter_principal_sets:
            query_params["filter_principal_sets"] = ",".join(filter_principal_sets)
        if bypass_visible_to:
            query_params["bypass_visible_to"] = bypass_visible_to

        data = search_client.search(
            index_id, q, advanced=advanced, limit=limit, query_params=query_params
        )
    elif query_document:
        doc = json.load(query_document)

        if limit:
            doc["limit"] = limit
        if advanced:
            doc["advanced"] = advanced
        if bypass_visible_to:
            doc["bypass_visible_to"] = bypass_visible_to
        if filter_principal_sets:
            doc["filter_principal_sets"] = filter_principal_sets

        data = search_client.post_search(index_id, doc)
    else:
        raise click.UsageError("Either '-q' or '--query-document' must be provided")

    # format such that TEXT mode is JSON output
    # because Globus Search data is user-supplied JSON, there is no other sensible way
    # to format the data
    formatted_print(data, text_format=FORMAT_TEXT_RAW)
