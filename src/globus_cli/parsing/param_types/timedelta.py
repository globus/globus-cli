import datetime
import re

import click

_timedelta_regex = re.compile(
    r"""
    ^
    \s*
    ((?P<weeks>\d+)w)?
    \s*
    ((?P<days>\d+)d)?
    \s*
    ((?P<hours>\d+)h)?
    \s*
    ((?P<minutes>\d+)m)?
    \s*
    ((?P<seconds>\d+)s?)?
    \s*
    $
    """,
    flags=re.VERBOSE,
)


class TimedeltaType(click.ParamType):
    """
    Parse a number of seconds, minutes, hours, days, and weeks from a string into a
    timedelta object
    """

    name = "TIMEDELTA"

    def __init__(self, *, convert_to_seconds: bool = True):
        self._convert_to_seconds = convert_to_seconds

    def convert(self, value, param, ctx):
        matches = _timedelta_regex.match(value)
        if not matches:
            self.fail(f"couldn't parse timedelta: '{value}'")
        delta = datetime.timedelta(
            **{k: int(v) for k, v in matches.groupdict(0).items()}
        )
        if self._convert_to_seconds:
            return int(delta.total_seconds())
        else:
            return delta
