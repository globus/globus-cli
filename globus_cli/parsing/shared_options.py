import click

from globus_cli.parsing.command_state import (
    format_option, debug_option, map_http_status_option,
    verbose_option, fields_option, HiddenOption)
from globus_cli.parsing.version_option import version_option
from globus_cli.parsing.case_insensitive_choice import CaseInsensitiveChoice
from globus_cli.parsing.detect_and_decorate import detect_and_decorate
from globus_cli.parsing.location import LocationType
from globus_cli.parsing.iso_time import ISOTimeType


def common_options(*args, **kwargs):
    """
    This is a multi-purpose decorator for applying a "base" set of options
    shared by all commands.
    It can be applied either directly, or given keyword arguments.

    Usage:

    >>> @common_options
    >>> def mycommand(abc, xyz):
    >>>     ...

    or

    >>> @common_options(no_format_option=True)
    >>> def mycommand(abc, xyz):
    >>>     ...
    """
    def decorate(f, **kwargs):
        """
        Work of actually decorating a function -- wrapped in here because we
        want to dispatch depending on how `common_options` is invoked
        """
        f = version_option(f)
        f = debug_option(f)
        f = verbose_option(f)
        f = click.help_option('-h', '--help')(f)

        # if the format option is being allowed, it needs to be applied to `f`
        if not kwargs.get('no_format_option'):
            f = format_option(f)

        # if the --map-http-status option is being allowed, ...
        if not kwargs.get('no_map_http_status_option'):
            f = map_http_status_option(f)

        # if the fields option is being allowed, ...
        if not kwargs.get("no_fields_option"):
            f = fields_option(f)

        return f

    return detect_and_decorate(decorate, args, kwargs)


def endpoint_id_arg(*args, **kwargs):
    """
    This is the `ENDPOINT_ID` argument consumed by many Transfer endpoint
    related operations. It accepts alternate metavars for cases when another
    name is desirable (e.x. `SHARE_ID`, `HOST_ENDPOINT_ID`), but can also be
    applied as a direct decorator if no specialized metavar is being passed.

    Usage:

    >>> @endpoint_id_arg
    >>> def command_func(endpoint_id):
    >>>     ...

    or

    >>> @endpoint_id_arg(metavar='HOST_ENDPOINT_ID')
    >>> def command_func(endpoint_id):
    >>>     ...
    """
    def decorate(f, **kwargs):
        """
        Work of actually decorating a function -- wrapped in here because we
        want to dispatch depending on how this is invoked
        """
        metavar = kwargs.get('metavar', 'ENDPOINT_ID')
        f = click.argument('endpoint_id', metavar=metavar, type=click.UUID)(f)
        return f

    return detect_and_decorate(decorate, args, kwargs)


def endpoint_create_and_update_params(*args, **kwargs):
    """
    Collection of options consumed by Transfer endpoint create and update
    operations -- accepts toggle regarding create vs. update that makes
    display_name required vs. optional.

    Usage:

    >>> @endpoint_create_and_update_params(create=True)
    >>> def command_func(display_name, description, info_link, contact_info,
    >>>                  contact_email, organization, department, keywords,
    >>>                  public, location, disable_verify, myproxy_dn,
    >>>                  myproxy_server, oauth_server, force_encryption,
    >>>                  default_directory, subscription_id, network_use,
    >>>                  max_concurrency, preferred_concurrency,
    >>>                  max_parallelism, preferred_parallelism):
    >>>     ...
    """
    def inner_decorator(f, create=False):
        update_help_prefix = (not create and 'New ') or ''

        # display name is required for create, not update
        if create:
            f = click.argument('display_name')(f)
        else:
            f = click.option(
                '--display-name',
                help=(update_help_prefix +
                      'Name for the endpoint'))(f)

        # Options available to any endpoint
        f = click.option(
            "--description",
            help=(update_help_prefix +
                  "Description for the endpoint"))(f)
        f = click.option(
            "--info-link",
            help=(update_help_prefix +
                  "Link for Info about the endpoint"))(f)
        f = click.option(
            "--contact-info",
            help=(update_help_prefix +
                  "Contact Info for the endpoint"))(f)
        f = click.option(
            "--contact-email",
            help=(update_help_prefix +
                  "Contact Email for the endpoint"))(f)
        f = click.option(
            "--organization",
            help=(update_help_prefix +
                  "Organization for the endpoint"))(f)
        f = click.option(
            "--department",
            help=(update_help_prefix +
                  "Department which operates the endpoint"))(f)
        f = click.option(
            "--keywords",
            help=(update_help_prefix +
                  "Comma seperated list of keywords to help searches"
                  "for the endpoint"))(f)
        f = click.option(
            "--default-directory",
            help=("Set the default directory"))(f)
        f = click.option(
            "--force-encryption/--no-force-encryption", default=None,
            help=("(Un)Force the endpoint to encrypt transfers"))(f)
        f = click.option(
            "--disable-verify/--no-disable-verify", is_flag=True,
            help="(Un)Set the endpoint to ignore checksum verification")(f)

        # GCS only options
        f = click.option(
            "--public/--private", "public", default=None,
            help=("Set the endpoint to be public or private "
                  "(Globus Connect Server only)"))(f)
        f = click.option(
            "--myproxy-dn",
            help=("Set the MyProxy Server DN (Globus Connect Server only)"))(f)
        f = click.option(
            "--myproxy-server",
            help=("Set the MyProxy Server URI "
                  "(Globus Connect Server only)"))(f)
        f = click.option(
            "--oauth-server",
            help=("Set the OAuth Server URI (Globus Connect Server only)"))(f)
        f = click.option(
            "--location", type=LocationType(), default=None,
            help="Manually set the endpoint's latitude and longitude "
                 "(Globus Connect Server only)")(f)

        # Managed Endpoint options
        f = click.option(
            "--subscription-id", type=click.UUID, default=None,
            cls=HiddenOption,
            help=("Set the endpoint as a managed endpoint with the given "
                  "subscription ID"))(f)
        f = click.option(
            "--network-use", default=None,
            type=click.Choice(["normal", "minimal", "aggressive", "custom"]),
            help=("Set the endpoint's network use level. If using custom, "
                  "the endpoint's max and preferred concurrency must be set "
                  "(Managed endpoints only) (Globus Connect Server only)"))(f)
        f = click.option(
            "--max-concurrency", type=int, default=None,
            help=("Set the endpoint's max concurrency "
                  "(Managed endpoints only) (Globus Connect Server only)"))(f)
        f = click.option(
            "--preferred-concurrency", type=int, default=None,
            help=("Set the endpoint's preferred concurrency "
                  "(Managed endpoints only) (Globus Connect Server only)"))(f)
        f = click.option(
            "--max-parallelism", type=int, default=None,
            help=("Set the endpoint's max parallelism "
                  "(Managed endpoints only) (Globus Connect Server only)"))(f)
        f = click.option(
            "--preferred-parallelism", type=int, default=None,
            help=("Set the endpoint's preferred parallelism "
                  "(Managed endpoints only) (Globus Connect Server only)"))(f)

        return f

    return detect_and_decorate(inner_decorator, args, kwargs)


def validate_endpoint_create_and_update_params(endpoint_type, managed, params):
    """
    Given an endpoint type of "shared" "server" or "personal" and option values
    Confirms the option values are valid for the given endpoint
    """
    # options only allowed for GCS endpoints
    if endpoint_type != "server":
        # catch params with two option flags
        if params["public"] is False:
            raise click.UsageError("Option --private only allowed "
                                   "for Globus Connect Server endpoints")
        # catch any params only usable with GCS
        for option in ["public", "myproxy_dn", "myproxy_server",
                       "oauth_server", "location", "network_use",
                       "max_concurrency", "preferred_concurrency",
                       "max_parallelism", "preferred_parallelism"]:
            if params[option] is not None:
                raise click.UsageError(
                    ("Option --{} can only be used with Globus Connect Server "
                     "endpoints".format(option.replace("_", "-"))))

    # if the endpoint was not previously managed, and is not being passed
    # a subscription id, it cannot use managed endpoint only fields
    if (not managed) and (not params["subscription_id"]):
        for option in ["network_use", "max_concurrency",
                       "preferred_concurrency", "max_parallelism",
                       "preferred_parallelism"]:
            if params[option] is not None:
                raise click.UsageError(
                    ("Option --{} can only be used with managed "
                     "endpoints".format(option.replace("_", "-"))))


def task_id_arg(*args, **kwargs):
    """
    This is the `TASK_ID` argument consumed by many Transfer Task operations.
    It accept a toggle on whether or not it is required

    Usage:

    >>> @task_id_option
    >>> def command_func(task_id):
    >>>     ...

    or

    >>> @task_id_option(required=False)
    >>> def command_func(task_id):
    >>>     ...

    By default, the task ID is made required; pass `required=False` to the
    decorator arguments to make it optional.
    """
    def inner_decorator(f, required=True):
        f = click.argument('TASK_ID', required=required)(f)
        return f
    return detect_and_decorate(inner_decorator, args, kwargs)


def task_submission_options(f):
    """
    Options shared by both transfer and delete task submission
    """
    f = click.option(
        "--dry-run", is_flag=True,
        help=("Don't actually submit the task, print submission "
              "data instead"))(f)
    f = click.option(
        "--submission-id", help=(
            "Task submission ID, as generated by `globus task "
            "generate-submission-id`. Used for safe resubmission in the "
            "presence of network failures."))(f)
    f = click.option(
        "--label", default=None, help="Set a label for this task.")(f)
    f = f = click.option(
        "--deadline", default=None, type=ISOTimeType(),
        help="Set a deadline for this to be canceled if not completed by.")(f)

    return f


def role_id_arg(f):
    """
    Unmodifiable `ROLE_ID` argument for Transfer Endpoint Role management.
    """
    return click.argument('role_id')(f)


def server_id_arg(f):
    """
    Unmodifiable `SERVER_ID` argument for Transfer Endpoint Server management.
    """
    return click.argument('server_id')(f)


def server_add_and_update_opts(*args, **kwargs):
    """
    shared collection of options for `globus transfer endpoint server add` and
    `globus transfer endpoint server update`.
    Accepts a toggle to know if it's being used as `add` or `update`.

    usage:

    >>> @server_add_and_update_opts
    >>> def command_func(subject, port, scheme, hostname):
    >>>     ...

    or

    >>> @server_add_and_update_opts(add=True)
    >>> def command_func(subject, port, scheme, hostname):
    >>>     ...
    """

    def port_range_callback(ctx, param, value):
        if not value:
            return None

        value = value.lower().strip()
        if value == 'unspecified':
            return None, None
        if value == 'unrestricted':
            return 1024, 65535

        try:
            lower, upper = map(int, value.split('-'))
        except ValueError:  # too many/few values from split or non-integer(s)
            raise click.BadParameter("must specify as 'unspecified', "
                                     "'unrestricted', or as range separated "
                                     "by a hyphen (e.g. '50000-51000')")
        if not 1024 <= lower <= 65535 or not 1024 <= upper <= 65535:
            raise click.BadParameter("must be within the 1024-65535 range")

        return (lower, upper) if lower <= upper else (upper, lower)

    def inner_decorator(f, add=False):
        f = click.option('--hostname', required=add,
                         help='Server Hostname.')(f)

        default_scheme = 'gsiftp' if add else None
        f = click.option(
            '--scheme', help='Scheme for the Server.',
            type=CaseInsensitiveChoice(('gsiftp', 'ftp')),
            default=default_scheme, show_default=add)(f)

        default_port = 2811 if add else None
        f = click.option(
            '--port', help='Port for Globus control channel connections.',
            type=int, default=default_port, show_default=add)(f)

        f = click.option(
            '--subject',
            help=('Subject of the X509 Certificate of the server. When '
                  'unspecified, the CN must match the server hostname.'))(f)

        for adjective, our_preposition, their_preposition in [
            ('incoming', 'to', 'from'),
            ('outgoing', 'from', 'to'),
        ]:
            f = click.option(
              '--{}-data-ports'.format(adjective),
              callback=port_range_callback,
              help="Indicate to firewall administrators at other sites how to "
                   "allow {} traffic {} this server {} their own. Specify as "
                   "either 'unspecified', 'unrestricted', or as range of "
                   "ports separated by a hyphen (e.g. '50000-51000') within "
                   "the 1024-65535 range.".format(adjective, our_preposition,
                                                  their_preposition)
            )(f)

        return f
    return detect_and_decorate(inner_decorator, args, kwargs)


def security_principal_opts(*args, **kwargs):
    def preprocess_security_principals(f):
        def decorator(*args, **kwargs):
            identity = kwargs.pop('identity', None)
            group = kwargs.pop('group', None)
            if kwargs.get('principal') is not None:
                if identity or group:
                    raise click.UsageError(
                        'You may only pass one security principal')
            else:
                if identity and group:
                    raise click.UsageError(
                        ('You have passed both an identity and a group. '
                         'Please only pass one principal type'))
                elif not identity and not group:
                    raise click.UsageError(
                        ('You must provide at least one principal '
                         '(identity, group, etc.)'))

                if identity:
                    kwargs['principal'] = ('identity', identity)
                else:
                    kwargs['principal'] = ('group', group)

            return f(*args, **kwargs)
        return decorator

    def inner_decorator(
            f, allow_anonymous=False, allow_all_authenticated=False):

        # order matters here -- the preprocessor must run after option
        # application, so it has to be applied first
        if isinstance(f, click.Command):
            # if we're decorating a command, put the preprocessor on its
            # callback, not on `f` itself
            f.callback = preprocess_security_principals(f.callback)
        else:
            # otherwise, we're applying to a function, but other decorators may
            # have been applied to give it params
            # so, copy __click_params__ to preserve those parameters
            oldfun = f
            f = preprocess_security_principals(f)
            f.__click_params__ = getattr(oldfun, '__click_params__', [])

        f = click.option('--identity', metavar='IDENTITY_ID_OR_NAME',
                         help='Identity to use as a security principal')(f)
        f = click.option('--group', metavar='GROUP_ID',
                         help='Group to use as a security principal')(f)

        if allow_anonymous:
            f = click.option(
                '--anonymous', 'principal', flag_value=('anonymous', ""),
                help=('Allow anyone access, even without logging in '
                      '(treated as a security principal)'))(f)
        if allow_all_authenticated:
            f = click.option(
                '--all-authenticated', 'principal',
                flag_value=('all_authenticated_users', ""),
                help=('Allow anyone access, as long as they login'
                      '(treated as a security principal)'))(f)

        return f

    return detect_and_decorate(inner_decorator, args, kwargs)
