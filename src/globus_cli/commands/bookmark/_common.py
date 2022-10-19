from __future__ import annotations

import typing as t
from uuid import UUID

import click
import globus_sdk


def resolve_id_or_name(
    client: globus_sdk.TransferClient, bookmark_id_or_name: str
) -> globus_sdk.GlobusHTTPResponse | dict[str, t.Any]:
    # leading/trailing whitespace doesn't make sense for UUIDs and the Transfer
    # service outright forbids it for bookmark names, so we can strip it off
    bookmark_id_or_name = bookmark_id_or_name.strip()

    res = None
    try:
        UUID(bookmark_id_or_name)  # raises ValueError if argument not a UUID
    except ValueError:
        pass
    else:
        try:
            res = client.get_bookmark(bookmark_id_or_name.lower())
        except globus_sdk.TransferAPIError as err:
            if err.code != "BookmarkNotFound":
                raise
    if res:
        return res

    # non-UUID input or UUID not found; fallback to match by name
    try:
        # n.b. case matters to the Transfer service for bookmark names, so
        # two bookmarks can exist whose names vary only by their case
        return t.cast(
            t.Dict[str, t.Any],
            next(
                bookmark_row
                for bookmark_row in client.bookmark_list()
                if bookmark_row["name"] == bookmark_id_or_name
            ),
        )

    except StopIteration:
        click.echo(f'No bookmark found for "{bookmark_id_or_name}"', err=True)
        click.get_current_context().exit(1)
