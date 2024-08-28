import typing as t

from globus_cli.termio import Field, formatters

from .client import CustomTransferClient
from .data import (
    add_batch_to_transfer_data,
    assemble_generic_doc,
    display_name_or_cname,
    iterable_response_to_dict,
)
from .recursive_ls import RecursiveLsResponse


class _NameFormatter(formatters.StrFormatter):
    def parse(self, value: t.Any) -> str:
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError("cannot parse display_name from malformed data")
        return str(value[0] or value[1])


ENDPOINT_LIST_FIELDS = [
    Field("ID", "id"),
    Field("Owner", "owner_string"),
    Field("Display Name", "[display_name, canonical_name]", formatter=_NameFormatter()),
]


__all__ = (
    "ENDPOINT_LIST_FIELDS",
    "CustomTransferClient",
    "RecursiveLsResponse",
    "display_name_or_cname",
    "iterable_response_to_dict",
    "assemble_generic_doc",
    "add_batch_to_transfer_data",
)
