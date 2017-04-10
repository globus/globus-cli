import warnings
import click
import jmespath

from globus_cli import config
from globus_cli.parsing.case_insensitive_choice import CaseInsensitiveChoice
from globus_cli.parsing.hidden_option import HiddenOption


# Format Enum for output formatting
# could use a namedtuple, but that's overkill
JSON_FORMAT = 'json'
TEXT_FORMAT = 'text'


class CommandState(object):
    def __init__(self):
        # default is config value, or TEXT if it's not set
        self.output_format = config.get_output_format() or TEXT_FORMAT
        # a jmespath expression to process on the json output
        self.jmespath_expr = None
        # default is always False
        self.debug = False
        # default is 0
        self.verbosity = 0
        # by default, empty dict
        self.http_status_map = {}
        # by default, empty list
        self.output_fields = []

    def outformat_is_text(self):
        return self.output_format == TEXT_FORMAT

    def outformat_is_json(self):
        return self.output_format == JSON_FORMAT

    def is_verbose(self):
        return self.verbosity > 0


def format_option(f):
    def callback(ctx, param, value):
        state = ctx.ensure_object(CommandState)
        # only set a new format if there is no stored jmespath expression
        # otherwise, it must remain JSON
        if state.jmespath_expr is None:
            # need to do an OR check here because this is invoked with
            # value=None everywhere that the `-F`/`--format` option is
            # omitted (each level of the command tree)
            state.output_format = (value or state.output_format).lower()
        return state.output_format

    def jmespath_callback(ctx, param, value):
        if value is None:
            return
        state = ctx.ensure_object(CommandState)
        state.output_format = 'json'
        state.jmespath_expr = jmespath.compile(value)
        return state.jmespath_expr

    f = click.option(
        '-F', '--format',
        type=CaseInsensitiveChoice([JSON_FORMAT, TEXT_FORMAT]),
        help='Output format for stdout. Defaults to text',
        expose_value=False, callback=callback)(f)
    f = click.option(
        "--jmespath", "--jq",
        help=("A JMESPath expression to apply to json output. "
              "Takes precedence over any specified '--format' and forces "
              "the format to be json processed by this expression"),
        expose_value=False, callback=jmespath_callback)(f)
    return f


def debug_option(f):
    def callback(ctx, param, value):
        if not value or ctx.resilient_parsing:
            # turn off warnings altogether
            warnings.simplefilter('ignore')
            return

        warnings.simplefilter('default')
        state = ctx.ensure_object(CommandState)
        state.debug = True
        config.setup_logging(level="DEBUG")

    return click.option(
        '--debug', is_flag=True, cls=HiddenOption,
        expose_value=False, callback=callback, is_eager=True)(f)


def verbose_option(f):
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
            config.setup_logging(level="ERROR")

        # verbosity level 2
        # warnings set to default
        # logging set to info
        if value == 2:
            warnings.simplefilter("default")
            config.setup_logging(level="INFO")

        # verbosity level 3+
        # warnings set to always
        # logging set to debug
        # sets debug flag to true
        if value >= 3:
            warnings.simplefilter("always")
            state.debug = True
            config.setup_logging(level="DEBUG")

    return click.option(
        "--verbose", "-v", count=True,
        expose_value=False, callback=callback, is_eager=True,
        help="Control level of output")(f)


def map_http_status_option(f):
    exit_stat_set = [0, 1] + list(range(50, 100))

    def per_val_callback(ctx, value):
        if value is None:
            return None
        state = ctx.ensure_object(CommandState)
        try:
            # we may be given a comma-delimited list of values
            # any cases of empty strings are dropped
            pairs = [x for x in
                     (y.strip() for y in value.split(','))
                     if len(x)]
            # iterate over those pairs, splitting them on `=` signs
            for http_stat, exit_stat in (pair.split('=') for pair in pairs):
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
                '--map-http-status must have an argument of the form '
                '"INT=INT,INT=INT,..." and values of exit codes must be in '
                '0,1,50-99')

    def callback(ctx, param, value):
        """
        Wrap the per-value callback -- multiple=True means that the value is
        always a tuple of given vals.
        """
        for v in value:
            per_val_callback(ctx, v)

    return click.option(
        '--map-http-status',
        help=('Map HTTP statuses to any of these exit codes: 0,1,50-99. '
              'e.g. "404=50,403=51"'),
        expose_value=False, callback=callback, multiple=True)(f)


def fields_option(f):
    def callback(ctx, param, value):
        """
        Split the comma separated list of fields into a list of fields.
        """
        state = ctx.ensure_object(CommandState)

        # allow caps and spaces, but force them into field names
        # this assumes all json fields use only lower case and have no spaces.
        if value:
            state.output_fields = value.split(",")

    return click.option(
        "--fields", expose_value=False, callback=callback,
        help="Comma separated list of fields to output")(f)
