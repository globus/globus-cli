import typing as t

from globus_cli.termio import Field, field_formatters

from .activation import (
    activation_requirements_help_text,
    autoactivate,
    supported_activation_methods,
)
from .client import CustomTransferClient
from .data import (
    add_batch_to_transfer_data,
    assemble_generic_doc,
    display_name_or_cname,
    iterable_response_to_dict,
)
from .delegate_proxy import fill_delegate_proxy_activation_requirements
from .recursive_ls import RecursiveLsResponse


class _DisplayNameFormatter(field_formatters.StrFieldFormatter):
    def parse(self, value: t.Any) -> str:
        if not isinstance(value, dict):
            raise ValueError("cannot parse display_name from non-dict data")
        return str(value["display_name"] or value["canonical_name"])


ENDPOINT_LIST_FIELDS = [
    Field("ID", "id"),
    Field("Owner", "owner_string"),
    Field("Display Name", "@", formatter=_DisplayNameFormatter()),
]


__all__ = (
    "ENDPOINT_LIST_FIELDS",
    "CustomTransferClient",
    "RecursiveLsResponse",
    "supported_activation_methods",
    "activation_requirements_help_text",
    "autoactivate",
    "fill_delegate_proxy_activation_requirements",
    "display_name_or_cname",
    "iterable_response_to_dict",
    "assemble_generic_doc",
    "add_batch_to_transfer_data",
)
