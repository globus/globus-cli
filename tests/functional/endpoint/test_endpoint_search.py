from __future__ import annotations

import random
import re
import typing as t
import urllib.parse
import uuid

import pytest
from globus_sdk.testing import RegisteredResponse, get_last_request


def _make_mapped_collection_search_result(
    collection_id: str,
    endpoint_id: str,
    display_name: str,
    owner_string: str,
    manager_fqdn: str,
    collection_fqdn: str,
) -> dict[str, t.Any]:
    # most of the fields are filled with dummy data
    # some of these values are pulled out here either to ensure their integrity
    # or to make them more visible to a reader
    username = "u_abcdefghijklmnop"  # not a real b32 username

    data = {
        "DATA_TYPE": "endpoint",
        "_rank": random.random() * 10,
        "authentication_timeout_mins": 15840,
        "canonical_name": f"u_{username}#{collection_id}",
        "default_directory": "/{server_default}/",
        "display_name": display_name,
        "entity_type": "GCSv5_mapped_collection",
        "expires_in": -1,
        "gcs_manager_url": f"https://{manager_fqdn}",
        "gcs_version": "5.4.50",
        "id": collection_id,
        "location": "Automatic",
        "max_concurrency": 4,
        "max_parallelism": 8,
        "my_effective_roles": [],
        "myproxy_server": "myproxy.globusonline.org",
        "name": collection_id,
        "network_use": "normal",
        "non_functional_endpoint_display_name": f"host of {display_name}",
        "non_functional_endpoint_id": endpoint_id,
        "owner_id": endpoint_id,
        "owner_string": owner_string,
        "preferred_concurrency": 2,
        "preferred_parallelism": 4,
        "public": True,
        "shareable": True,
        "tlsftp_server": f"tlsftp://{collection_fqdn}:443",
        "username": username,
    }
    # there are so many null and False values in a typical item, handling them
    # separately makes the document above more readable
    null_keys = {
        "acl_max_expiration_period_mins",
        "authentication_assurance_timeout",
        "authentication_policy_id",
        "contact_email",
        "contact_info",
        "department",
        "description",
        "expire_time",
        "gcp_connected",
        "gcp_paused",
        "globus_connect_setup_key",
        "host_endpoint",
        "host_endpoint_display_name",
        "host_endpoint_id",
        "host_path",
        "https_server",
        "info_link",
        "keywords",
        "last_accessed_time",
        "local_user_info_available",
        "mapped_collection_display_name",
        "mapped_collection_id",
        "myproxy_dn",
        "oauth_server",
        "organization",
        "s3_url",
        "sharing_target_endpoint",
        "sharing_target_root_path",
        "subscription_id",
        "user_message",
        "user_message_link",
    }
    false_keys = {
        "acl_available",
        "acl_editable",
        "activated",
        "disable_anonymous_writes",
        "disable_verify",
        "force_encryption",
        "force_verify",
        "french_english_bilingual",
        "high_assurance",
        "in_use",
        "is_globus_connect",
        "mfa_required",
        "non_functional",
        "requester_pays",
        "s3_owner_activated",
    }
    # sanity check that we're not overwriting anything
    assert null_keys & false_keys == set()
    assert null_keys & set(data) == set()
    assert false_keys & set(data) == set()

    for k in null_keys:
        data[k] = None
    for k in false_keys:
        data[k] = False
    return data


@pytest.fixture
def singular_search_response():
    collection_id = str(uuid.uuid4())
    endpoint_id = str(uuid.uuid4())
    display_name = "dummy result"
    owner_string = "globus@globus.org"
    manager_fqdn = "a0bc1.23de.data.globus.org"
    collection_fqdn = f"m-f45678.{manager_fqdn}"

    return RegisteredResponse(
        service="transfer",
        path="/v0.10/endpoint_search",
        metadata={
            "collection_id": collection_id,
            "endpoint_id": endpoint_id,
            "display_name": display_name,
            "owner_string": owner_string,
            "collection_fqdn": collection_fqdn,
        },
        json={
            "DATA": [
                _make_mapped_collection_search_result(
                    collection_id,
                    endpoint_id,
                    display_name,
                    owner_string,
                    manager_fqdn,
                    collection_fqdn,
                )
            ],
            "DATA_TYPE": "endpoint_list",
            "has_next_page": False,
            "limit": 25,
            "offset": 0,
        },
    )


def test_search_shows_collection_id(run_line, singular_search_response):
    singular_search_response.add()
    meta = singular_search_response.metadata

    result = run_line("globus endpoint search mytestquery")

    # the output format should be
    #   HEADER_LINE\nSEPARATOR_LINE\nDATA_LINES\n
    #
    # trim off that trailing newline, and then inspect
    lines = result.output.rstrip("\n").split("\n")
    # there should be exactly one line of data, so length is 3
    assert len(lines) == 3
    header_line, separator_line, data_line = lines

    # the header line shows the field names in order
    header_row = [header.strip() for header in re.split(r"\s+\|\s+", header_line)]
    assert header_row == ["ID", "Owner", "Display Name", "Domain"]
    # the separator line is a series of dashes
    separator_row = re.split(r"\s+\|\s+", separator_line)
    assert len(separator_row) == 4
    for separator in separator_row:
        assert set(separator) == {"-"}  # exactly one character is used

    # the data row should have the collection ID, Owner, Display Name, and Domain
    data_row = re.split(r"\s+\|\s+", data_line)
    assert data_row == [
        meta["collection_id"],
        meta["owner_string"],
        meta["display_name"],
        meta["collection_fqdn"],
    ]

    # final sanity check -- the endpoint ID for a mapped collection doesn't
    # appear anywhere in the output
    assert meta["endpoint_id"] not in result.output


@pytest.mark.parametrize(
    "entity_type",
    (
        "GCP_mapped_collection",
        "GCP_guest_collection",
        "GCSv5_endpoint",
        "GCSv5_mapped_collection",
        "GCSv5_guest_collection",
    ),
)
def test_search_can_send_entity_type_parameter(
    run_line, singular_search_response, entity_type
):
    singular_search_response.add()
    run_line(
        [
            "globus",
            "endpoint",
            "search",
            "mytestquery",
            "--filter-entity-type",
            entity_type,
        ]
    )

    # confirm that the entity type is sent in the query string
    last_req = get_last_request()
    parsed_qs = urllib.parse.parse_qs(urllib.parse.urlparse(last_req.url).query)
    assert "filter_entity_type" in parsed_qs
    sent_filter_entity_type = parsed_qs["filter_entity_type"]
    assert sent_filter_entity_type == [entity_type]


@pytest.mark.parametrize(
    "entity_type",
    (
        pytest.param("GCP_MAPPED_COLLECTION", id="denormed-upper"),
        pytest.param("gcsv5_endpoint", id="denmormed-lower"),
    ),
)
def test_search_sends_normalized_case_entity_type_param(
    run_line, singular_search_response, entity_type
):
    singular_search_response.add()
    run_line(
        [
            "globus",
            "endpoint",
            "search",
            "mytestquery",
            "--filter-entity-type",
            entity_type,
        ]
    )

    normalized_entity_type = entity_type[:3].upper() + entity_type[3:].lower()

    # confirm that the entity type is sent in the query string
    last_req = get_last_request()
    parsed_qs = urllib.parse.parse_qs(urllib.parse.urlparse(last_req.url).query)
    assert "filter_entity_type" in parsed_qs
    sent_filter_entity_type = parsed_qs["filter_entity_type"]
    assert sent_filter_entity_type == [normalized_entity_type]
