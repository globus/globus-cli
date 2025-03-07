from __future__ import annotations

import globus_sdk
import globus_sdk.gare

from globus_cli.termio import PrintableErrorField, write_error_info
from globus_cli.types import JsonValue

from ..messages import pretty_json
from ..registry import sdk_error_handler


@sdk_error_handler(
    error_class="SearchAPIError",
    condition=lambda err: err.code == "BadRequest.ValidationError",
)
def searchapi_validationerror_hook(exception: globus_sdk.SearchAPIError) -> None:
    fields = [
        PrintableErrorField("HTTP status", exception.http_status),
        PrintableErrorField("request_id", exception.request_id),
        PrintableErrorField("code", exception.code),
        PrintableErrorField("message", exception.message, multiline=True),
    ]
    error_data: dict[str, JsonValue] | None = exception.error_data
    if error_data is not None:
        messages = error_data.get("messages")
        if isinstance(messages, dict) and len(messages) == 1:
            error_location, details = next(iter(messages.items()))
            fields += [
                PrintableErrorField("location", error_location),
                PrintableErrorField("details", pretty_json(details), multiline=True),
            ]
        elif messages is not None:
            fields += [
                PrintableErrorField("details", pretty_json(messages), multiline=True)
            ]

    write_error_info("Search API Error", fields)


@sdk_error_handler(error_class="SearchAPIError")
def searchapi_hook(exception: globus_sdk.SearchAPIError) -> None:
    fields = [
        PrintableErrorField("HTTP status", exception.http_status),
        PrintableErrorField("request_id", exception.request_id),
        PrintableErrorField("code", exception.code),
        PrintableErrorField("message", exception.message, multiline=True),
    ]
    error_data: dict[str, JsonValue] | None = exception.error_data
    if error_data is not None:
        fields += [
            PrintableErrorField("error_data", pretty_json(error_data, compact=True))
        ]

    write_error_info("Search API Error", fields)
