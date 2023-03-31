from __future__ import annotations

import abc
import dataclasses
import shutil
import typing as t

import click
import globus_sdk

from .context import should_show_server_timing

_BORDER_COLOR = "blue"
_FILL_COLOR = "yellow"


class ServerTimingParseError(ValueError):
    pass


@dataclasses.dataclass
class Metric:
    name: str
    # although surprising, the spec allows for metrics with no duration value
    # the canonical example is 'miss' (undecorated) to indicate a cache miss
    duration: t.Optional[float] = None
    description: t.Optional[str] = None


def maybe_show_server_timing(res: globus_sdk.GlobusHTTPResponse) -> None:
    if not should_show_server_timing():
        return

    server_timing_str = res.headers.get("Server-Timing")
    if server_timing_str:
        # for now, always use the default parser and ignore malformed metric items
        # in the future, this could be extended to try different parsers in series
        metrics = DEFAULT_PARSER.parse_metric_header(
            server_timing_str, skip_errors=True
        )
        render_metrics_onscreen(metrics)


def render_metrics_onscreen(metrics: list[Metric]) -> None:
    click.echo("Server Timing Info", err=True)
    term_width = shutil.get_terminal_size((80, 20)).columns
    use_width = term_width - 4

    items = sorted(
        (
            (f"{m.description or m.name}={m.duration}", m.duration)
            for m in metrics
            if m.duration is not None
        ),
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


class ServerTimingParser(abc.ABC):
    # which version of the Server-Timing spec does this parser implement?
    spec_reference: t.ClassVar[str]

    @abc.abstractmethod
    def parse_single_metric(self, metric_str: str) -> Metric:
        ...

    def parse_metric_header(
        self, header_str: str, skip_errors: bool = True
    ) -> list[Metric]:
        metric_items = header_str.split(",")
        ret: list[Metric] = []
        for item in metric_items:
            try:
                ret.append(self.parse_single_metric(item))
            except ServerTimingParseError:
                if not skip_errors:
                    raise
        return ret


class Draft2017Parser(ServerTimingParser):
    """
    Parsing per the Server-Timing draft from 2017 and earlier
    The spec has changed since this draft.

    For example

      'a=1; "alpha", b=2, c, d; "delta"'

    will parse as

    Metrics:
      - name: a
        description: alpha
        duration: 1.0
      - name: b
        duration: 2.0
      - name: c
      - name: d
        description: delta
    """

    spec_reference = "https://www.w3.org/TR/2017/WD-server-timing-20171018/"

    def parse_single_metric(self, metric_str: str) -> Metric:
        part, *optionals = (p.strip() for p in metric_str.split(";"))
        if len(optionals) > 1:
            raise ServerTimingParseError(
                "Too many semicolons in timing item, cannot parse"
            )
        metric = _parse_simple_metric_part(part)
        if optionals:
            metric.description = optionals[0].strip('"')
        return metric


def _parse_simple_metric_part(metric: str) -> Metric:
    if not metric:
        raise ServerTimingParseError("encountered empty metric")

    if "=" not in metric:
        return Metric(name=metric)

    name, _, unparsed_value = metric.partition("=")
    try:
        value = float(unparsed_value)
    except ValueError as e:
        raise ServerTimingParseError("Metric value did not parse as float") from e
    return Metric(name=name, duration=value)


DEFAULT_PARSER = Draft2017Parser()
