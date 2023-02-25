import json
import uuid
from io import TextIOWrapper

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, TextMode, display

from ._common import index_id_arg


@command("ingest", short_help="Ingest a document into Globus Search")
@index_id_arg
@click.argument("DOCUMENT", type=click.File("r"))
@LoginManager.requires_login("search")
def ingest_command(
    *, login_manager: LoginManager, index_id: uuid.UUID, document: TextIOWrapper
):
    """
    Submit a Globus Search 'GIngest' document, to be indexed in a Globus Search Index.
    You must have 'owner', 'admin', or 'writer' permissions on that index.

    The document can be provided either as a filename, or via stdin. To use stdin, pass
    a single hyphen for the document name, as in

    \b
        globus search ingest $INDEX_ID -

    The document can be a complete GIngest document, a GMetaList, or a GMetaEntry.
    The datatype is taken from the `@datatype` field, with a default of `GIngest`.

    On success, the response will contain a Task ID, which can be used to monitor the
    Ingest Task.
    """
    search_client = login_manager.get_search_client()
    doc = json.load(document)

    datatype = doc.get("@datatype", "GIngest")
    if datatype not in ("GIngest", "GMetaList", "GMetaEntry"):
        raise click.UsageError(f"Unsupported datatype: '{datatype}'")

    # if the document is not a GIngest doc, wrap it in one for submission to the API
    if datatype != "GIngest":
        doc = {"@datatype": "GIngest", "ingest_type": datatype, "ingest_data": doc}

    display(
        search_client.ingest(index_id, doc),
        text_mode=TextMode.text_record,
        fields=[Field("Task ID", "task_id"), Field("Acknowledged", "acknowledged")],
    )
