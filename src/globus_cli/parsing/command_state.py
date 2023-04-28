from __future__ import annotations

import logging.config
import typing as t
import warnings

import click

# Format Enum for output formatting
# could use a namedtuple, but that's overkill
JSON_FORMAT = "json"
TEXT_FORMAT = "text"
UNIX_FORMAT = "unix"

F = t.TypeVar("F", bound=t.Union[t.Callable, click.Command])


def _setup_logging(level="DEBUG"):
    conf = {
        "version": 1,
        "formatters": {
            "basic": {
                "format": (
                    "[%(levelname)s] [%(asctime)s] "
                    "%(name)s::%(funcName)s() %(message)s"
                )
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "basic",
            }
        },
        "loggers": {
            "globus_sdk": {"level": level, "handlers": ["console"]},
            "globus_cli": {"level": level, "handlers": ["console"]},
        },
    }

    logging.config.dictConfig(conf)


class CommandState:
    def __init__(self) -> None:
        # init takes no params and sets everything to defaults
        self.output_format: str = TEXT_FORMAT
        # a jmespath expression to process on the json output
        self.jmespath_expr: t.Any | None = None
        self.debug: bool = False
        self.verbosity: int = 0
        self.http_status_map: dict[int, int] = {}
        self.show_server_timing: bool = False

    def outformat_is_text(self) -> bool:
        return self.output_format == TEXT_FORMAT

    def outformat_is_json(self) -> bool:
        return self.output_format == JSON_FORMAT

    def outformat_is_unix(self) -> bool:
        return self.output_format == UNIX_FORMAT

    def is_verbose(self) -> bool:
        return self.verbosity > 0


def format_option(f: F) -> F:
    def callback(ctx, param, value):
        if not value:
            return

        state = ctx.ensure_object(CommandState)

        # when a jmespath expr is set, ignore --format=text
        if value == TEXT_FORMAT and state.jmespath_expr:
            return

        state.output_format = value.lower()

    def jmespath_callback(ctx, param, value):
        if value is None:
            return

        import jmespath

        state = ctx.ensure_object(CommandState)
        state.jmespath_expr = jmespath.compile(value)

        if state.output_format == TEXT_FORMAT:
            state.output_format = JSON_FORMAT

    f = click.option(
        "-F",
        "--format",
        type=click.Choice(
            [UNIX_FORMAT, JSON_FORMAT, TEXT_FORMAT], case_sensitive=False
        ),
        help="Output format for stdout. Defaults to text",
        expose_value=False,
        callback=callback,
    )(f)
    f = click.option(
        "--jmespath",
        "--jq",
        help=(
            "A JMESPath expression to apply to json output. "
            "Forces the format to be json processed by this expression"
        ),
        expose_value=False,
        callback=jmespath_callback,
    )(f)
    return f


def debug_option(f: F) -> F:
    def callback(ctx, param, value):
        if not value or ctx.resilient_parsing:
            # turn off warnings altogether
            warnings.simplefilter("ignore")
            return

        warnings.simplefilter("default")
        state = ctx.ensure_object(CommandState)
        state.debug = True
        _setup_logging(level="DEBUG")

    return click.option(
        "--debug",
        is_flag=True,
        hidden=True,
        expose_value=False,
        callback=callback,
        is_eager=True,
    )(f)


def verbose_option(f: F) -> F:
    def callback(ctx, param, value):
        # set state verbosity value from option
        state = ctx.ensure_object(CommandState)
        state.verbosity = value

        # no verbosity
        # all warnings are ignored
        # logging is not turned on
        if value == 0:
            warnings.simplefilter("ignore")

        # verbosity level 1
        # warnings set to once
        # logging set to error
        if value == 1:
            warnings.simplefilter("once")
            _setup_logging(level="ERROR")

        # verbosity level 2
        # warnings set to default
        # logging set to info
        if value == 2:
            warnings.simplefilter("default")
            _setup_logging(level="INFO")

        # verbosity level 3+
        # warnings set to always
        # logging set to debug
        # sets debug flag to true
        if value >= 3:
            warnings.simplefilter("always")
            state.debug = True
            _setup_logging(level="DEBUG")

    return click.option(
        "--verbose",
        "-v",
        count=True,
        expose_value=False,
        callback=callback,
        is_eager=True,
        help="Control level of output",
    )(f)


def map_http_status_option(f: F) -> F:
    exit_stat_set = [0, 1] + list(range(50, 100))

    def per_val_callback(ctx, value):
        if value is None:
            return None
        state = ctx.ensure_object(CommandState)
        try:
            # we may be given a comma-delimited list of values
            # any cases of empty strings are dropped
            pairs = [x for x in (y.strip() for y in value.split(",")) if len(x)]
            # iterate over those pairs, splitting them on `=` signs
            for http_stat, exit_stat in (pair.split("=") for pair in pairs):
                # "parse" as ints
                http_stat, exit_stat = int(http_stat), int(exit_stat)
                # force into the desired range
                if exit_stat not in exit_stat_set:
                    raise ValueError()
                # map the status
                state.http_status_map[http_stat] = exit_stat
        # two conditions can cause ValueError: split didn't give right number
        # of args, or results weren't int()-able
        except ValueError:
            raise click.UsageError(
                "--map-http-status must have an argument of the form "
                '"INT=INT,INT=INT,..." and values of exit codes must be in '
                "0,1,50-99"
            )

    def callback(ctx, param, value):
        """
        Wrap the per-value callback -- multiple=True means that the value is
        always a tuple of given vals.
        """
        for v in value:
            per_val_callback(ctx, v)

    return click.option(
        "--map-http-status",
        help=(
            "Map HTTP statuses to any of these exit codes: 0,1,50-99. "
            'e.g. "404=50,403=51"'
        ),
        expose_value=False,
        callback=callback,
        multiple=True,
    )(f)


def show_server_timing_option(f: F) -> F:
    def callback(ctx, param, value):
        if not value:
            return
        state = ctx.ensure_object(CommandState)
        state.show_server_timing = True

    return click.option(
        "--show-server-timing",
        is_flag=True,
        hidden=True,
        expose_value=False,
        callback=callback,
    )(f)
