from __future__ import annotations

import globus_sdk

from globus_cli.termio import PrintableErrorField, write_error_info

from ..messages import emit_unauthorized_message
from ..registry import sdk_error_handler


@sdk_error_handler(
    error_class="TransferAPIError",
    condition=lambda err: err.code == "ClientError.AuthenticationFailed",
)
def transfer_unauthenticated_hook(exception: globus_sdk.TransferAPIError) -> None:
    emit_unauthorized_message()


@sdk_error_handler(error_class="TransferAPIError")
def transferapi_hook(exception: globus_sdk.TransferAPIError) -> None:
    write_error_info(
        "Transfer API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("request_id", exception.request_id),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )
