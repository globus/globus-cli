import uuid

import pytest

from globus_cli.services.gcs import ConnectorIdFormatter


@pytest.mark.parametrize(
    "connector_id, connector_name",
    [
        ("145812c8-decc-41f1-83cf-bb2a85a2a70b", "POSIX"),
        ("7e3f3f5e-350c-4717-891a-2f451c24b0d4", "BlackPearl"),
        ("7c100eae-40fe-11e9-95a3-9cb6d0d9fd63", "Box"),
        ("1b6374b0-f6a4-4cf7-a26f-f262d9c6ca72", "Ceph"),
        ("28ef55da-1f97-11eb-bdfd-12704e0d6a4d", "OneDrive"),
        ("976cf0cf-78c3-4aab-82d2-7c16adbcc281", "Google Drive"),
        ("56366b96-ac98-11e9-abac-9cb6d0d9fd63", "Google Cloud Storage"),
        ("7251f6c8-93c9-11eb-95ba-12704e0d6a4d", "ActiveScale"),
        ("7643e831-5f6c-4b47-a07f-8ee90f401d23", "S3"),
        ("052be037-7dda-4d20-b163-3077314dc3e6", "POSIX Staging"),
        ("e47b6920-ff57-11ea-8aaa-000c297ab3c2", "iRODS"),
    ],
)
def test_connector_id_to_name_formatting(connector_id, connector_name):
    assert ConnectorIdFormatter().format(connector_id) == connector_name


def test_name_of_unknown_connector_id():
    fake_id = str(uuid.UUID(int=0))
    assert ConnectorIdFormatter().format(fake_id) == f"UNKNOWN ({fake_id})"
