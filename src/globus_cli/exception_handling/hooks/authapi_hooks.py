from __future__ import annotations

import globus_sdk

from globus_cli.termio import PrintableErrorField, write_error_info

from ..messages import emit_unauthorized_message
from ..registry import sdk_error_handler


@sdk_error_handler(
    error_class="AuthAPIError", condition=lambda err: err.code == "UNAUTHORIZED"
)
def authapi_unauthenticated_hook(exception: globus_sdk.AuthAPIError) -> None:
    emit_unauthorized_message()


@sdk_error_handler(
    error_class="AuthAPIError",
    condition=lambda err: err.message == "invalid_grant",
)
def invalidrefresh_hook(exception: globus_sdk.AuthAPIError) -> None:
    emit_unauthorized_message()


@sdk_error_handler(error_class="AuthAPIError")
def authapi_hook(exception: globus_sdk.AuthAPIError) -> None:
    write_error_info(
        "Auth API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )
