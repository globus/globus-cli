from uuid import UUID

import click
from globus_sdk.exc import TransferAPIError
from globus_cli.services.transfer import get_client
from globus_cli.safeio import safeprint


def resolve_bookmark_id_or_name(bookmark_id_or_name):
    # leading/trailing whitespace doesn't make sense for UUIDs and the Transfer
    # service outright forbids it for bookmark names, so we can strip it off
    bookmark_id_or_name = bookmark_id_or_name.strip()
    client = get_client()

    res = None
    try:
        UUID(bookmark_id_or_name)  # raises ValueError if argument not a UUID
    except ValueError:
        pass
    else:
        try:
            res = client.get_bookmark(bookmark_id_or_name.lower())
        except TransferAPIError as exception:
            if exception.code != 'BookmarkNotFound':
                raise

    if not res:  # non-UUID input or UUID not found; fallback to match by name
        try:
            # n.b. case matters to the Transfer service for bookmark names, so
            # two bookmarks can exist whose names vary only by their case
            res = next(bookmark_row for bookmark_row in client.bookmark_list()
                       if bookmark_row['name'] == bookmark_id_or_name)

        except StopIteration:
            safeprint('No bookmark found for "{}"'.format(bookmark_id_or_name),
                      write_to_stderr=True)
            click.get_current_context().exit(1)

    return res
