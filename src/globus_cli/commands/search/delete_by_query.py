from __future__ import annotations

import json
import uuid
from io import TextIOWrapper
from typing import Any

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, mutex_option_group
from globus_cli.termio import FORMAT_TEXT_RECORD, formatted_print

from ._common import index_id_arg


@command("delete-by-query", short_help="Perform a delete-by-query")
@click.option("-q", help="The query-string to use to search the index.")
@click.option(
    "--query-document",
    type=click.File("r"),
    help="A complete query document to use to search the index.",
)
@click.option(
    "--advanced",
    is_flag=True,
    help="Perform the search using the advanced query syntax",
)
@index_id_arg
@mutex_option_group("-q", "--query-document")
@LoginManager.requires_login(LoginManager.SEARCH_RS)
def delete_by_query_command(
    *,
    login_manager: LoginManager,
    index_id: uuid.UUID,
    q: str | None,
    query_document: TextIOWrapper | None,
    advanced: bool,
):
    """
    Perform a Delete-By-Query on a Globus Search Index using either a simple query
    string or a complex query document. The operation will be submitted as a task and
    can be monitored via the task_id returned.

    At least one of `-q` or `--query-document` must be provided.
    If a query document and command-line options are provided, the options used will
    override any options which were present on the query document.
    """
    search_client = login_manager.get_search_client()

    if q:
        doc: dict[str, Any] = {"q": q}
    elif query_document:
        doc = json.load(query_document)
    else:
        raise click.UsageError("Either '-q' or '--query-document' must be provided")

    if advanced:
        doc["advanced"] = advanced

    data = search_client.delete_by_query(index_id, doc)
    formatted_print(
        data,
        text_format=FORMAT_TEXT_RECORD,
        fields=[
            ("Message", lambda _x: "delete-by-query task successfully submitted"),
            ("Task ID", "task_id"),
        ],
    )
