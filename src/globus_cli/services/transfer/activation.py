from __future__ import annotations

import globus_sdk


def supported_activation_methods(
    res: globus_sdk.GlobusHTTPResponse,
) -> list[str]:
    """
    Given an activation_requirements document
    returns a list of activation methods supported by this endpoint.
    """
    supported = ["web"]  # web activation is always supported.

    # oauth
    if res["oauth_server"]:
        supported.append("oauth")

    for req in res["DATA"]:
        # myproxy
        if (
            req["type"] == "myproxy"
            and req["name"] == "hostname"
            and req["value"] != "myproxy.globusonline.org"
        ):
            supported.append("myproxy")

    return supported
