from __future__ import annotations

import typing as t
import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    JSONStringOrFile,
    ParsedJSONData,
    command,
    mutex_option_group,
)
from globus_cli.termio import Field, TextMode, display, formatters

from ._common import index_id_arg


@command("delete-by-query", short_help="Perform a delete-by-query")
@click.option("-q", help="The query-string to use to search the index.")
@click.option(
    "--query-document",
    type=JSONStringOrFile(),
    help="A complete query document to use to search the index.",
)
@click.option(
    "--advanced",
    is_flag=True,
    help="Perform the search using the advanced query syntax",
)
@index_id_arg
@mutex_option_group("-q", "--query-document")
@LoginManager.requires_login("search")
def delete_by_query_command(
    *,
    login_manager: LoginManager,
    index_id: uuid.UUID,
    q: str | None,
    query_document: ParsedJSONData | None,
    advanced: bool,
) -> None:
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
        doc: dict[str, t.Any] = {"q": q}
    elif query_document is not None:
        if not isinstance(query_document.data, dict):
            raise click.UsageError(
                "--query-document cannot contain non-object JSON data"
            )
        doc = query_document.data
    else:
        raise click.UsageError("Either '-q' or '--query-document' must be provided")

    if advanced:
        doc["advanced"] = advanced

    data = search_client.delete_by_query(index_id, doc)
    display(
        data,
        text_mode=TextMode.text_record,
        fields=[
            Field(
                "Message",
                "@",
                formatter=formatters.StaticStringFormatter(
                    "delete-by-query task successfully submitted"
                ),
            ),
            Field("Task ID", "task_id"),
        ],
    )
