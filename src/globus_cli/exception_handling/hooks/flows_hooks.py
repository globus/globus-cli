from __future__ import annotations

import textwrap
import typing as t

import globus_sdk
import globus_sdk.gare

from globus_cli.termio import PrintableErrorField, write_error_info

from ..messages import emit_message_for_gare, pretty_json
from ..registry import sdk_error_handler


@sdk_error_handler(
    error_class="FlowsAPIError",
    condition=lambda err: globus_sdk.gare.is_gare(err.raw_json or {}),
    exit_status=4,
)
def handle_flows_gare(exception: globus_sdk.FlowsAPIError) -> int | None:
    gare = globus_sdk.gare.to_gare(exception.raw_json or {})
    if not gare:
        raise ValueError("Expected a GARE, but got None")

    emit_message_for_gare(gare)
    return None


@sdk_error_handler(
    error_class="FlowsAPIError",
    condition=lambda err: err.code == "UNPROCESSABLE_ENTITY",
)
def flows_validation_error_hook(exception: globus_sdk.FlowsAPIError) -> None:
    # we know the data must be a dict because `code` parsed (condition above)
    error_data: dict[str, t.Any] = exception.raw_json  # type: ignore[assignment]

    # try to pull the details array, empty on failure
    details_list: list[dict[str, t.Any]] = []
    try:
        detail = error_data["error"]["detail"]
        if isinstance(detail, list):
            details_list = detail
    except KeyError:
        pass

    # try to pull the 'message' string into a list of fields to render
    message_fields: list[PrintableErrorField] = []
    try:
        message_fields = [
            PrintableErrorField("message", error_data["error"]["message"])
        ]
    except KeyError:
        pass

    # if there are multiple details or we couldn't get a message
    # then rewrite the messages to display as formatted pydantic error data
    if len(details_list) > 1 or not message_fields:
        num_errors = len(details_list)
        # try to extract 'loc' and 'msg' from the details, but only
        # update 'message_fields' if the data are present
        try:
            messages = [
                f"{_jsonpath_from_pydantic_loc(data['loc'])}: {data['msg']}"
                for data in details_list
            ]
        except KeyError:
            pass
        else:
            message_fields = [
                PrintableErrorField(
                    "message", f"{num_errors} validation errors", multiline=True
                ),
                PrintableErrorField(
                    "errors",
                    "\n".join(messages),
                    multiline=True,
                ),
            ]

    # ultimate fallback: get the SDK's interpreted message
    # this only applies if neither $.error.message nor $.error.detail worked
    if not message_fields:
        message_fields = [PrintableErrorField("message", exception.message)]

    write_error_info(
        "Flows API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            *message_fields,
        ],
    )


@sdk_error_handler(error_class="FlowsAPIError")
def flows_error_hook(exception: globus_sdk.FlowsAPIError) -> None:
    assert exception.raw_json is not None  # Influence mypy's knowledge of `raw_json`.
    details: list[dict[str, t.Any]] | str = exception.raw_json["error"]["detail"]
    detail_fields: list[PrintableErrorField] = []

    # if the detail is a string, return that as a single field
    if isinstance(details, str):
        if len(details) > 120:
            details = textwrap.fill(details, width=80)
        detail_fields = [PrintableErrorField("detail", details, multiline=True)]
    # if it's a list of objects, wrap them into a multiline detail field
    elif isinstance(details, list):
        num_errors = len(details)
        if all((isinstance(d, dict) and "loc" in d and "msg" in d) for d in details):
            detail_strings = [
                (
                    ((data["type"] + " ") if "type" in data else "")
                    + f"{_jsonpath_from_pydantic_loc(data['loc'])}: {data['msg']}"
                )
                for data in details
            ]
            if num_errors == 1:
                detail_fields = [PrintableErrorField("detail", detail_strings[0])]
            else:
                detail_fields = [
                    PrintableErrorField("detail", f"{num_errors} errors"),
                    PrintableErrorField(
                        "errors",
                        "\n".join(detail_strings),
                        multiline=True,
                    ),
                ]
        else:
            detail_fields = [
                PrintableErrorField(
                    "detail",
                    "\n".join(pretty_json(detail, compact=True) for detail in details),
                    multiline=True,
                )
            ]

    fields = [
        PrintableErrorField("HTTP status", exception.http_status),
        PrintableErrorField("code", exception.code),
    ]
    if "message" in exception.raw_json["error"]:
        fields.append(
            PrintableErrorField("message", exception.raw_json["error"]["message"])
        )
    fields.extend(detail_fields)

    write_error_info("Flows API Error", fields)


_JSONPATH_SPECIAL_CHARS = "[]'\"\\."
_JSONPATH_ESCAPE_MAP = str.maketrans(
    {
        "'": "\\'",
        "\\": "\\\\",
    }
)


def _jsonpath_from_pydantic_loc(loc: list[str | int]) -> str:
    """
    Given a 'loc' from pydantic error data, convert it into a JSON Path expression.

    Takes the following steps:
    - turns integers into integer indices
    - turns most strings into dotted access
    - turns strings containing special characters into single-quoted bracket access
      with ' and \\ escaped
    """
    path = "$"
    for part in loc:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            if any(c in part for c in _JSONPATH_SPECIAL_CHARS):
                part = f"'{part.translate(_JSONPATH_ESCAPE_MAP)}'"
                path += f"[{part}]"
            else:
                path += f".{part}"
    return path
