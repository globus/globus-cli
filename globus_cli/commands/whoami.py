import click

from globus_cli.safeio import (
    safeprint, formatted_print, FORMAT_TEXT_RECORD, FORMAT_TEXT_RAW)
from globus_cli.parsing import common_options
from globus_cli.helpers import is_verbose
from globus_cli.config import (
    WHOAMI_ID_OPTNAME, WHOAMI_USERNAME_OPTNAME,
    WHOAMI_EMAIL_OPTNAME, WHOAMI_NAME_OPTNAME,
    GLOBUS_ENV, lookup_option)


@click.command('whoami',
               help=('Show the currently logged-in identity.'))
@common_options(no_map_http_status_option=True)
def whoami_command():
    """
    Executor for `globus whoami`
    """

    username = lookup_option(WHOAMI_USERNAME_OPTNAME,
                             environment=GLOBUS_ENV)
    if not username:
        safeprint('No login information available. Please try '
                  'logging in again.', write_to_stderr=True)
        click.get_current_context().exit(1)

    fields = tuple((x, x) for x in ('Username', 'Name', 'ID', 'Email'))
    formatted_print({
            'Username': username,
            'Name': lookup_option(WHOAMI_NAME_OPTNAME, environment=GLOBUS_ENV),
            'ID': lookup_option(WHOAMI_ID_OPTNAME, environment=GLOBUS_ENV),
            'Email': lookup_option(WHOAMI_EMAIL_OPTNAME,
                                   environment=GLOBUS_ENV)
        }, fields=fields,
        text_format=(FORMAT_TEXT_RECORD if is_verbose() else FORMAT_TEXT_RAW),
        response_key=None if is_verbose() else 'Username')
