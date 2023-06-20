from __future__ import annotations

import typing as t

import click

from globus_cli.constants import EXPLICIT_NULL
from globus_cli.endpointish import EntityType

C = t.TypeVar("C", bound=t.Union[t.Callable, click.Command])


def validate_endpoint_create_and_update_params(
    entity_type: EntityType, managed: bool, params: dict
) -> None:
    """
    Given an endpoint type and option values

    Confirms the option values are valid for the given endpoint

    NOTE: this is a legacy method which only applies to GCSv4 and GCP
    """
    # options only allowed for GCSv4 endpoints
    if entity_type != EntityType.GCSV4_HOST:
        # catch any params only usable with GCS
        for option in [
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
            if params.get(option) is not None:
                raise click.UsageError(
                    f"Option --{option.replace('_', '-')} can only be used with "
                    "Globus Connect Server endpoints"
                )

    # if the endpoint was not previously managed, and is not being passed
    # a subscription id, it cannot use managed endpoint only fields
    if (not managed) and not (params.get("subscription_id") or params.get("managed")):
        for option in [
            "network_use",
            "max_concurrency",
            "preferred_concurrency",
            "max_parallelism",
            "preferred_parallelism",
        ]:
            if params.get(option) is not None:
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
    if params.get("network_use") != "custom":
        for option in custom_network_use_params:
            if params.get(option) is not None:
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
