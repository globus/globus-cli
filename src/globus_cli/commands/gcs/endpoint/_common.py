from __future__ import annotations

import typing as t

from globus_cli.termio import Field, formatters
from globus_cli.termio.formatters import FieldFormatter


class NetworkUseFormatter(FieldFormatter[t.Union[str, t.Tuple[int, int]]]):
    """
    Custom Formatter to make network use associated fields better grouped.

    Data is expected to be passed as a list of three elements:
      [network_use, preferred, max]

    Examples:
      ("custom", 1, 2) -> "Preferred: 1, Max: 2"
      ("aggressive", None, None) -> "aggressive"
      ("normal", None, 3) -> "normal"
    """

    def parse(self, value: t.Any) -> str | tuple[int, int]:
        if isinstance(value, list) and len(value) == 3:
            if value[0] == "custom":
                if isinstance(value[1], int) and isinstance(value[2], int):
                    return value[1], value[2]
            elif isinstance(value[0], str):
                return value[0]

        raise ValueError(
            f"Invalid network use data shape. Expected [str, int, int]; found {value}."
        )

    def render(self, value: str | tuple[int, int]) -> str:
        if isinstance(value, tuple):
            return f"Preferred: {value[0]}, Max: {value[1]}"
        return value


# https://docs.globus.org/globus-connect-server/v5.4/api/schemas/Endpoint_1_2_0_schema/
GCS_ENDPOINT_FIELDS = [
    Field("Endpoint ID", "id"),
    Field("Display Name", "display_name"),
    Field("Allow UDT", "allow_udt", formatter=formatters.FuzzyBool),
    Field("Contact Email", "contact_email"),
    Field("Contact Info", "contact_info"),
    Field("Department", "department"),
    Field("Description", "description"),
    Field("Earliest Last Access", "earliest_last_access", formatter=formatters.Date),
    Field("GCS Manager URL", "gcs_manager_url"),
    Field("GridFTP Control Channel Port", "gridftp_control_channel_port"),
    Field("Info Link", "info_link"),
    Field("Keywords", "keywords", formatter=formatters.Array),
    Field("Network Use", "network_use"),
    Field(
        "Network Use (Concurrency)",
        "[network_use, preferred_concurrency, max_concurrency]",
        formatter=NetworkUseFormatter(),
    ),
    Field(
        "Network Use (Parallelism)",
        "[network_use, preferred_parallelism, max_parallelism]",
        formatter=NetworkUseFormatter(),
    ),
    Field("Organization", "organization"),
    Field("Public", "public", formatter=formatters.FuzzyBool),
    Field("Subscription ID", "subscription_id"),
]
