from __future__ import annotations

import functools
from typing import Callable

import click


def server_id_arg(f):
    return click.argument("server_id")(f)


def server_add_and_update_opts(f: Callable | None = None, *, add=False):
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

    if f is None:
        return functools.partial(server_add_and_update_opts, add=add)

    def port_range_callback(ctx, param, value):
        if not value:
            return None

        value = value.lower().strip()
        if value == "unspecified":
            return None, None
        if value == "unrestricted":
            return 1024, 65535

        try:
            lower, upper = map(int, value.split("-"))
        except ValueError:  # too many/few values from split or non-integer(s)
            raise click.BadParameter(
                "must specify as 'unspecified', "
                "'unrestricted', or as range separated "
                "by a hyphen (e.g. '50000-51000')"
            )
        if not 1024 <= lower <= 65535 or not 1024 <= upper <= 65535:
            raise click.BadParameter("must be within the 1024-65535 range")

        return (lower, upper) if lower <= upper else (upper, lower)

    if add:
        f = click.argument("HOSTNAME")(f)
    else:
        f = click.option("--hostname", help="Server Hostname.")(f)

    default_scheme = "gsiftp" if add else None
    f = click.option(
        "--scheme",
        help="Scheme for the Server.",
        type=click.Choice(("gsiftp", "ftp"), case_sensitive=False),
        default=default_scheme,
        show_default=add,
    )(f)

    default_port = 2811 if add else None
    f = click.option(
        "--port",
        help="Port for Globus control channel connections.",
        type=int,
        default=default_port,
        show_default=add,
    )(f)

    f = click.option(
        "--subject",
        help=(
            "Subject of the X509 Certificate of the server. When "
            "unspecified, the CN must match the server hostname."
        ),
    )(f)

    for adjective, our_preposition, their_preposition in [
        ("incoming", "to", "from"),
        ("outgoing", "from", "to"),
    ]:
        f = click.option(
            f"--{adjective}-data-ports",
            callback=port_range_callback,
            help="Indicate to firewall administrators at other sites how to "
            "allow {} traffic {} this server {} their own. Specify as "
            "either 'unspecified', 'unrestricted', or as range of "
            "ports separated by a hyphen (e.g. '50000-51000') within "
            "the 1024-65535 range.".format(
                adjective, our_preposition, their_preposition
            ),
        )(f)

    return f
