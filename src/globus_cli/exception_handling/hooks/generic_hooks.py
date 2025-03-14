from __future__ import annotations

import json

import click
import globus_sdk

from globus_cli.termio import PrintableErrorField, outformat_is_json, write_error_info

from ..registry import sdk_error_handler


@sdk_error_handler(
    error_class="GlobusAPIError", condition=lambda err: err.raw_json is None
)
def null_data_error_handler(exception: globus_sdk.GlobusAPIError) -> None:
    write_error_info(
        "GlobusAPINullDataError",
        [PrintableErrorField("error_type", exception.__class__.__name__)],
    )


@sdk_error_handler(
    error_class="GlobusAPIError", condition=lambda err: outformat_is_json()
)
def json_error_handler(exception: globus_sdk.GlobusAPIError) -> None:
    msg = json.dumps(exception.raw_json, indent=2, separators=(",", ": "))
    click.secho(msg, fg="yellow", err=True)


@sdk_error_handler()  # catch-all
def globusapi_hook(exception: globus_sdk.GlobusAPIError) -> None:
    write_error_info(
        "Globus API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )


@sdk_error_handler(error_class="GlobusError")
def globus_error_hook(exception: globus_sdk.GlobusError) -> None:
    write_error_info(
        "Globus Error",
        [
            PrintableErrorField("error_type", exception.__class__.__name__),
            PrintableErrorField("message", str(exception), multiline=True),
        ],
    )
