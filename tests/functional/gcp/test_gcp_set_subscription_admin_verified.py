import pytest
from globus_sdk.testing import (
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

    with pytest.raises(Exception) as excinfo:
        run_line(
            [
                "globus",
                "gcp",
                "set-subscription-admin-verified",
                meta["collection_id_fail"],
                "true",
            ]
        )

    exc_val_str = str(excinfo.value)

    assert "exited with 1 when expecting 0" in exc_val_str

    assert (
        "User does not have an admin role on the collection's subscription "
        + "to set subscription_admin_verified.\n"
    ) in exc_val_str
