from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk

from globus_cli.constants import ExplicitNullType
from globus_cli.parsing import TaskPath, mutex_option_group
from globus_cli.utils import shlex_process_stream


def add_batch_to_transfer_data(
    source_base_path: str | None,
    dest_base_path: str | None,
    checksum_algorithm: str | None,
    transfer_data: globus_sdk.TransferData,
    batch: t.TextIO,
) -> None:
    @click.command()
    @click.option("--external-checksum")
    @click.option("--recursive", "-r", is_flag=True)
    @click.argument("source_path", type=TaskPath(base_dir=source_base_path))
    @click.argument("dest_path", type=TaskPath(base_dir=dest_base_path))
    @mutex_option_group("--recursive", "--external-checksum")
    def process_batch_line(dest_path, source_path, recursive, external_checksum):
        """
        Parse a line of batch input and turn it into a transfer submission
        item.
        """
        transfer_data.add_item(
            str(source_path),
            str(dest_path),
            external_checksum=external_checksum,
            checksum_algorithm=checksum_algorithm,
            recursive=recursive,
        )

    shlex_process_stream(process_batch_line, batch)


def display_name_or_cname(ep_doc: dict | globus_sdk.GlobusHTTPResponse) -> str:
    return t.cast(str, ep_doc["display_name"] or ep_doc["canonical_name"])


def iterable_response_to_dict(iterator):
    output_dict = {"DATA": []}
    for item in iterator:
        dat = item
        try:
            dat = item.data
        except AttributeError:
            pass
        output_dict["DATA"].append(dat)
    return output_dict


def assemble_generic_doc(datatype, **kwargs):
    doc = {"DATA_TYPE": datatype}
    for key, val in kwargs.items():
        if isinstance(val, uuid.UUID):
            val = str(val)

        if val is not None:
            doc[key] = ExplicitNullType.nullify(val)
    return doc
