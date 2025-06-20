from globus_sdk._testing import (
    load_response_set,
)


def test_gcp_set_subscription_admin_verified_success(run_line):
    meta = load_response_set("cli.gcp_set_subscription_admin_verified").metadata
    result = run_line(
        [
            "globus",
            "gcp",
            "set-subscription-admin-verified",
            meta["collection_id_success"],
            "false",
        ]
    )
    assert result.output == "Endpoint updated successfully\n"


def test_gcp_set_subscription_admin_verified_fail(run_line):
    meta = load_response_set("cli.gcp_set_subscription_admin_verified").metadata
    result = run_line(
        [
            "globus",
            "gcp",
            "set-subscription-admin-verified",
            meta["collection_id_fail"],
            "true",
        ]
    )
    assert result.output == (
        "User does not have an admin role on the collection's subscription "
        + "to set subscription_admin_verified.\n"
    )
