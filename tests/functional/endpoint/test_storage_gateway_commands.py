import globus_sdk
from globus_sdk.testing import get_response_set, load_response_set


def test_storage_gateway_list(add_gcs_login, run_line):
    load_response_set(globus_sdk.GCSClient.get_storage_gateway_list)
    get_response_set(globus_sdk.AuthClient.get_identities).lookup("default").add()

    meta = load_response_set("cli.collection_operations").metadata
    ep_id = meta["endpoint_id"]
    add_gcs_login(ep_id)

    line = f"globus endpoint storage-gateway list {ep_id}"
    result = run_line(line)

    print(result.output)

    expected = (
        "ID                                   | Display Name      | High Assurance | Allowed Domains\n"  # noqa: E501
        "-------------------------------------+-------------------+----------------+----------------\n"  # noqa: E501
        "a0cbde58-0183-11ea-92bd-9cb6d0d9fd63 | example gateway 1 | False          | example.edu    \n"  # noqa: E501
        "6840c8ba-eb98-11e9-b89c-9cb6d0d9fd63 | example gateway 2 | False          | example.edu    \n"  # noqa: E501
    )
    assert expected == result.output
