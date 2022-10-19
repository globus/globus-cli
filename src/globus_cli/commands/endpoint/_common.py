from __future__ import annotations

import typing as t

import click

from globus_cli.constants import EXPLICIT_NULL
from globus_cli.parsing import LocationType, MutexInfo, mutex_option_group

C = t.TypeVar("C", bound=t.Union[t.Callable, click.Command])


def _apply_create_or_update_params(f: C) -> C:
    f = click.option(
        "--force-encryption/--no-force-encryption",
        default=None,
        help="Force the endpoint to encrypt transfers",
    )(f)
    f = click.option(
        "--disable-verify/--no-disable-verify",
        default=None,
        is_flag=True,
        help="Set the endpoint to ignore checksum verification",
    )(f)

    # GCS only options
    gcsonly = "(Globus Connect Server only)"
    f = click.option(
        "--public/--private",
        "public",
        default=None,
        help=f"Set the endpoint to be public or private {gcsonly}",
    )(f)
    f = click.option("--myproxy-dn", help=f"Set the MyProxy Server DN {gcsonly}")(f)
    f = click.option("--myproxy-server", help=f"Set the MyProxy Server URI {gcsonly}")(
        f
    )
    f = click.option("--oauth-server", help=f"Set the OAuth Server URI {gcsonly}")(f)
    f = click.option(
        "--location",
        type=LocationType(),
        default=None,
        help=f"Manually set the endpoint's latitude and longitude {gcsonly}",
    )(f)

    # Managed Endpoint options
    f = click.option(
        "--managed",
        "managed",
        is_flag=True,
        flag_value=True,
        default=None,
        help=(
            "Set the endpoint as a managed endpoint. Requires the "
            "user to be a subscription manager. If the user has "
            "multiple subscription IDs, --subscription-id must be used "
            "instead"
        ),
    )(f)
    f = click.option(
        "--no-managed",
        "managed",
        is_flag=True,
        flag_value=False,
        default=None,
        help=(
            "Unset the endpoint as a managed endpoint. "
            "Does not require the user to be a subscription manager. "
            "Mutually exclusive with --subscription-id"
        ),
    )(f)
    f = click.option(
        "--subscription-id",
        type=click.UUID,
        default=None,
        help="Set the endpoint as a managed endpoint with the given "
        "subscription ID. Mutually exclusive with --no-managed",
    )(f)
    f = mutex_option_group(
        "--subscription-id",
        MutexInfo(
            "--no-managed", param="managed", present=lambda d: d.get("managed") is False
        ),
    )(f)

    managedonly = "(Managed endpoints only)"
    f = click.option(
        "--network-use",
        default=None,
        type=click.Choice(["normal", "minimal", "aggressive", "custom"]),
        help=(
            "Set the endpoint's network use level. If using custom, "
            "the endpoint's max and preferred concurrency and "
            f"parallelism must be set {managedonly} {gcsonly}"
        ),
    )(f)
    f = click.option(
        "--max-concurrency",
        type=int,
        default=None,
        help="Set the endpoint's max concurrency; requires --network-use=custom "
        f"{managedonly} {gcsonly}",
    )(f)
    f = click.option(
        "--preferred-concurrency",
        type=int,
        default=None,
        help="Set the endpoint's preferred concurrency; requires --network-use=custom "
        f"{managedonly} {gcsonly}",
    )(f)
    f = click.option(
        "--max-parallelism",
        type=int,
        default=None,
        help="Set the endpoint's max parallelism; requires --network-use=custom "
        f"{managedonly} {gcsonly}",
    )(f)
    f = click.option(
        "--preferred-parallelism",
        type=int,
        default=None,
        help="Set the endpoint's preferred parallelism; requires --network-use=custom "
        f"{managedonly} {gcsonly}",
    )(f)
    return f


def endpoint_create_params(f: C) -> C:
    return _apply_create_or_update_params(f)


def endpoint_update_params(f: C) -> C:
    f = click.option(
        "--no-default-directory",
        is_flag=True,
        flag_value=True,
        default=None,
        help="Unset any default directory on the endpoint",
    )(f)
    f = mutex_option_group("--default-directory", "--no-default-directory")(f)
    f = _apply_create_or_update_params(f)
    return f


def validate_endpoint_create_and_update_params(
    endpoint_type: str, managed: bool, params: dict
) -> None:
    """
    Given an endpoint type of "shared" "server" or "personal" and option values
    Confirms the option values are valid for the given endpoint
    """
    # options only allowed for GCS endpoints
    if endpoint_type != "server":
        # catch params with two option flags
        if params["public"] is False:
            raise click.UsageError(
                "Option --private only allowed for Globus Connect Server endpoints"
            )
        # catch any params only usable with GCS
        for option in [
            "public",
            "myproxy_dn",
            "myproxy_server",
            "oauth_server",
            "location",
            "network_use",
            "max_concurrency",
            "preferred_concurrency",
            "max_parallelism",
            "preferred_parallelism",
        ]:
            if params[option] is not None:
                raise click.UsageError(
                    f"Option --{option.replace('_', '-')} can only be used with "
                    "Globus Connect Server endpoints"
                )

    # if the endpoint was not previously managed, and is not being passed
    # a subscription id, it cannot use managed endpoint only fields
    if (not managed) and not (params["subscription_id"] or params["managed"]):
        for option in [
            "network_use",
            "max_concurrency",
            "preferred_concurrency",
            "max_parallelism",
            "preferred_parallelism",
        ]:
            if params[option] is not None:
                raise click.UsageError(
                    f"Option --{option.replace('_', '-')} can only be used with "
                    "managed endpoints"
                )

    # because the Transfer service doesn't do network use level updates in a
    # patchy way, *both* endpoint `POST`s *and* `PUT`s must either use
    # - `network_use='custom'` with *every* other parameter specified (which
    #   is validated by the service), or
    # - a preset/absent `network_use` with *no* other parameter specified
    #   (which is *not* validated by the service; in this case, Transfer will
    #   accept but ignore the others parameters if given, leading to user
    #   confusion if we don't do this validation check)
    custom_network_use_params = (
        "max_concurrency",
        "preferred_concurrency",
        "max_parallelism",
        "preferred_parallelism",
    )
    if params["network_use"] != "custom":
        for option in custom_network_use_params:
            if params[option] is not None:
                raise click.UsageError(
                    "The {} options require you use --network-use=custom.".format(
                        "/".join(
                            "--" + option.replace("_", "-")
                            for option in custom_network_use_params
                        )
                    )
                )

    # resolve the subscription_id value if "managed" was set
    # if --managed given pass --subscription-id or DEFAULT
    # if --no-managed given, pass explicit null
    managed_flag = params.get("managed")
    if managed_flag is not None:
        params.pop("managed")
        if managed_flag:
            params["subscription_id"] = params.get("subscription_id") or "DEFAULT"
        else:
            params["subscription_id"] = EXPLICIT_NULL

    # if --no-default-directory given, pass an EXPLICIT_NULL
    if params.get("no_default_directory"):
        params["default_directory"] = EXPLICIT_NULL
        params.pop("no_default_directory")
