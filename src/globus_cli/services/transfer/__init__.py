import typing as t

from globus_cli.termio import Field, formatters

from .client import CustomTransferClient
from .data import (
    add_batch_to_transfer_data,
    assemble_generic_doc,
    iterable_response_to_dict,
)
from .recursive_ls import RecursiveLsResponse


class _NameFormatter(formatters.StrFormatter):
    def parse(self, value: t.Any) -> str:
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError("cannot parse display_name from malformed data")
        return str(value[0] or value[1])


class _DomainFormatter(formatters.StrFormatter):
    def parse(self, value: t.Any) -> str:
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError("cannot parse domain from malformed data")

        tlsftp_server, gcs_manager_url = value

        # if tlsftp_server is present, this is a GCS collection
        # parse tlsftp_server in the format tlsftp://{domain}:{port}
        if tlsftp_server:
            assert isinstance(tlsftp_server, str)
            return tlsftp_server[len("tlsftp://") :].split(":")[0]

        # if gcs_manager_url present, but not tlsftp_server, this is a GCS endpoint
        # parse gcs_manager_url in the format https://{domain}
        elif gcs_manager_url:
            assert isinstance(gcs_manager_url, str)
            return gcs_manager_url[len("https://") :]

        # entity type with no domain
        else:
            return str(None)


DOMAIN_FIELD = Field(
    "Domain", "[tlsftp_server, gcs_manager_url]", formatter=_DomainFormatter()
)


ENDPOINT_LIST_FIELDS = [
    Field("ID", "id"),
    Field("Owner", "owner_string"),
    Field("Display Name", "[display_name, canonical_name]", formatter=_NameFormatter()),
    DOMAIN_FIELD,
]


__all__ = (
    "ENDPOINT_LIST_FIELDS",
    "DOMAIN_FIELD",
    "CustomTransferClient",
    "RecursiveLsResponse",
    "iterable_response_to_dict",
    "assemble_generic_doc",
    "add_batch_to_transfer_data",
)
