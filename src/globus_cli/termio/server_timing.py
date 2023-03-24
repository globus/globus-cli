from __future__ import annotations

import os
import shutil

import click
import globus_sdk

_BORDER_COLOR = "blue"
_FILL_COLOR = "yellow"


class ServerTimingParseError(ValueError):
    pass


def timing_string_to_dict(server_timing_string: str) -> dict[str, float]:
    """
    Given a Server Timing value as a string, parse it into a dict of the format
      nice_name: value

    For example

      'a=1, "alpha"; b=2'

    will parse as

      {"alpha": 1, "b": 2}

    """

    def parse_item(item: str) -> tuple[str, float]:
        item = [x.strip() for x in item.split(";")]
        if len(item) > 2:
            raise ServerTimingParseError(
                "Too many semicolons in timing item, cannot parse"
            )
        nice_name = None
        if len(item) == 2:
            nice_name = item[1].strip('"')
            item = item[0]
        item = item.split("=")
        if len(item) != 2:
            raise ServerTimingParseError("Wrong number of '=' delimited values")
        if not nice_name:
            nice_name = item[0]
        return (nice_name, float(item[1]))

    items = [x.strip() for x in server_timing_string.split(",")]
    return {key: value for (key, value) in [parse_item(x) for x in items]}


def render_timing_dict_onscreen(timing_dict: dict[str, tuple[str, float]]) -> None:
    click.echo("Server Timing Info", err=True)
    term_width = shutil.get_terminal_size((80, 20)).columns
    use_width = term_width - 4

    items = sorted(
        ((f"{name}={duration}", duration) for (name, duration) in timing_dict.items()),
        key=lambda x: x[1],
    )
    last = items[-1]
    factor = last[1]
    desc_width = (max(len(x[0]) for x in items) if items else 0) + 1

    hborder = click.style(f"+{'-' * (use_width + 2)}+", fg=_BORDER_COLOR)
    vborder = click.style("|", fg=_BORDER_COLOR)
    click.echo(hborder, err=True)

    for desc, size in items:
        desc = desc.ljust(desc_width, ".")
        bar_width = max(int((use_width - desc_width) * size / factor), 1)
        bar = "#" * bar_width
        msg = desc + click.style(bar, fg=_FILL_COLOR)
        style_char_length = len(msg) - len(click.unstyle(msg))
        msg = msg.ljust(use_width + style_char_length, " ")
        click.echo(f"{vborder} {msg} {vborder}", err=True)
    click.echo(hborder, err=True)


def maybe_show_server_timing(res: globus_sdk.GlobusHTTPResponse) -> None:
    if os.getenv("GLOBUS_CLI_SHOW_SERVER_TIMING") != "1":
        return

    try:
        parsed_timing = timing_string_to_dict(res.headers["Server-Timing"])
    except (ServerTimingParseError, KeyError):
        pass
    else:
        render_timing_dict_onscreen(parsed_timing)
