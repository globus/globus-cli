import pytest

from globus_cli.endpointish import EntityType


@pytest.mark.parametrize(
    "doc,expected",
    [
        ({}, EntityType.UNRECOGNIZED),
        ({"entity_type": "foo"}, EntityType.UNRECOGNIZED),
        ({"entity_type": "GCP_mapped_collection"}, EntityType.GCP_MAPPED),
        ({"entity_type": "GCP_guest_collection"}, EntityType.GCP_GUEST),
        ({"entity_type": "GCSv5_endpoint"}, EntityType.GCSV5_ENDPOINT),
        ({"entity_type": "GCSv5_mapped_collection"}, EntityType.GCSV5_MAPPED),
        ({"entity_type": "GCSv5_guest_collection"}, EntityType.GCSV5_GUEST),
        ({"entity_type": "GCSv4_host"}, EntityType.GCSV4_HOST),
        ({"entity_type": "GCSv4_share"}, EntityType.GCSV4_SHARE),
    ],
)
def test_determine_entity_type(doc, expected):
    assert EntityType.determine_entity_type(doc) == expected
