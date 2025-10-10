import pytest
from globus_sdk.testing import load_response_set


@pytest.mark.parametrize(
    "principal",
    (
        "--anonymous",
        "--all-authenticated",
        "--group 2c9a8a6b-b0b7-4f30-acc4-37e741a311c7",
        "--identity 7c939269-fafe-43d4-bbb5-d4e6321643a8",
    ),
)
def test_endpoint_permission_create_with_standard_principals(run_line, principal):
    meta = load_response_set("cli.endpoint_operations").metadata
    ep_id = meta["endpoint_id"]

    result = run_line(
        f"globus endpoint permission create {ep_id}:/ --permissions r {principal}"
    )
    assert "Access rule created successfully" in result.output


def test_endpoint_permission_create_with_no_principal(run_line):
    ep_id = "4c799ca5-6525-44d0-8887-a4bece7f4e09"

    run_line(
        f"globus endpoint permission create {ep_id}:/ --permissions r",
        assert_exit_code=2,
    )
