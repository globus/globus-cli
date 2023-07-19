from __future__ import annotations

import typing as t

import click

from globus_cli.parsing import AnnotatedOption
from globus_cli.types import TupleType

C = t.TypeVar("C", bound=t.Union[t.Callable[..., t.Any], click.Command])


def server_id_arg(f: C) -> C:
    return click.argument("server_id")(f)


def server_add_opts(f: C) -> C:
    f = click.argument("HOSTNAME")(f)
    return _server_add_and_update_opts(f, default_scheme="gsiftp", default_port=2811)


def server_update_opts(f: C) -> C:
    f = click.option("--hostname", help="Server Hostname.")(f)
    return _server_add_and_update_opts(f, default_scheme=None, default_port=None)


def _server_add_and_update_opts(
    f: C, *, default_scheme: str | None, default_port: int | None
) -> C:
    """
    shared collection of options for `globus transfer endpoint server add` and
    `globus transfer endpoint server update`.
    """

    def port_range_callback(
        ctx: click.Context, param: click.Parameter, value: t.Any
    ) -> tuple[int | None, int | None] | None:
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

    f = click.option(
        "--scheme",
        help="Scheme for the Server.",
        type=click.Choice(("gsiftp", "ftp"), case_sensitive=False),
        default=default_scheme,
        show_default=default_scheme is not None,
    )(f)

    f = click.option(
        "--port",
        help="Port for Globus control channel connections.",
        type=int,
        default=default_port,
        show_default=default_port is not None,
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
            cls=AnnotatedOption,
            # mypy flags this as an unexpected number of arguments to a TypeAlias, but
            # TupleType aliases t.Tuple/tuple which is variadic
            # TypeVarTuple will make this more possible to support, but it's
            # "experimental" in mypy at this time
            type_annotation=t.Optional[
                TupleType[t.Optional[int], t.Optional[int]]  # type: ignore[type-arg]
            ],
            help="Indicate to firewall administrators at other sites how to "
            "allow {} traffic {} this server {} their own. Specify as "
            "either 'unspecified', 'unrestricted', or as range of "
            "ports separated by a hyphen (e.g. '50000-51000') within "
            "the 1024-65535 range.".format(
                adjective, our_preposition, their_preposition
            ),
        )(f)

    return f
