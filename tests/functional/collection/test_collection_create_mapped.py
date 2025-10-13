import re
import uuid

import pytest
from globus_sdk.testing import load_response, register_response_set


@pytest.fixture(scope="session")
def identity_info():
    return {
        "username": "gargamel@globus.org",
        "id": str(uuid.UUID(int=5)),
        "name": "Gargamel Smurfnapper",
        # Azrael is his cat
        "organization": "Friends of Azrael",
    }


@pytest.fixture(scope="session", autouse=True)
def _register_responses(identity_info):
    storage_gateway_id = str(uuid.uuid4())
    collection_id = str(uuid.uuid4())
    endpoint_id = str(uuid.uuid4())

    username = identity_info["username"]
    domain = username.partition("@")[2]

    register_response_set(
        "cli.collection_create_mapped.storage_gateway_list",
        {
            "default": {
                "service": "gcs",
                "path": "/storage_gateways",
                "method": "GET",
                "json": {
                    "DATA_TYPE": "result#1.0.0",
                    "code": "success",
                    "data": [
                        {
                            "DATA_TYPE": "storage_gateway#1.2.0",
                            "admin_managed_credentials": False,
                            "allowed_domains": [domain],
                            "authentication_timeout_mins": 15840,
                            "connector_id": "145812c8-decc-41f1-83cf-bb2a85a2a70b",
                            "display_name": "localposix",
                            "high_assurance": False,
                            "id": storage_gateway_id,
                            "policies": {"DATA_TYPE": "posix_storage_policies#1.0.0"},
                            "require_high_assurance": False,
                            "require_mfa": False,
                        }
                    ],
                    "detail": "success",
                    "has_next_page": False,
                    "http_response_code": 200,
                },
                "metadata": {
                    "storage_gateway_id": storage_gateway_id,
                    "domain": domain,
                },
            },
            "multiple": {
                "service": "gcs",
                "path": "/storage_gateways",
                "method": "GET",
                "json": {
                    "DATA_TYPE": "result#1.0.0",
                    "code": "success",
                    "data": [
                        {
                            "DATA_TYPE": "storage_gateway#1.2.0",
                            "admin_managed_credentials": False,
                            "allowed_domains": [domain],
                            "authentication_timeout_mins": 15840,
                            "connector_id": "145812c8-decc-41f1-83cf-bb2a85a2a70b",
                            "display_name": "localposix",
                            "high_assurance": False,
                            "id": storage_gateway_id,
                            "policies": {"DATA_TYPE": "posix_storage_policies#1.0.0"},
                            "require_high_assurance": False,
                            "require_mfa": False,
                        },
                        {
                            "DATA_TYPE": "storage_gateway#1.2.0",
                            "admin_managed_credentials": False,
                            "allowed_domains": [domain],
                            "authentication_timeout_mins": 15840,
                            "connector_id": "145812c8-decc-41f1-83cf-bb2a85a2a70b",
                            "display_name": "localposix2",
                            "high_assurance": False,
                            "id": str(uuid.uuid4()),
                            "policies": {"DATA_TYPE": "posix_storage_policies#1.0.0"},
                            "require_high_assurance": False,
                            "require_mfa": False,
                        },
                    ],
                    "detail": "success",
                    "has_next_page": False,
                    "http_response_code": 200,
                },
                "metadata": {
                    "storage_gateway_id": storage_gateway_id,
                    "domain": domain,
                },
            },
            "empty": {
                "service": "gcs",
                "path": "/storage_gateways",
                "method": "GET",
                "json": {
                    "DATA_TYPE": "result#1.0.0",
                    "code": "success",
                    "data": [],
                    "detail": "success",
                    "has_next_page": False,
                    "http_response_code": 200,
                },
            },
        },
    )

    register_response_set(
        "cli.collection_create_mapped.mapped_collection_create",
        {
            "default": {
                "service": "gcs",
                "path": "/collections",
                "method": "POST",
                "json": {
                    "DATA_TYPE": "result#1.0.0",
                    "code": "success",
                    "data": [
                        {
                            "DATA_TYPE": "collection#1.9.0",
                            "allow_guest_collections": False,
                            "authentication_timeout_mins": 15840,
                            "collection_type": "mapped",
                            "connector_id": "145812c8-decc-41f1-83cf-bb2a85a2a70b",
                            "contact_email": username,
                            "created_at": "2023-12-12",
                            "delete_protected": True,
                            "disable_anonymous_writes": False,
                            "disable_verify": False,
                            "display_name": "myposix",
                            "domain_name": "foo.abc.xyz.data.globus.org",
                            "enable_https": True,
                            "force_encryption": False,
                            "force_verify": False,
                            "high_assurance": False,
                            "https_url": None,
                            "id": collection_id,
                            "identity_id": identity_info["id"],
                            "last_access": None,
                            "manager_url": "https://abc.xyz.data.globus.org",
                            "policies": {
                                "DATA_TYPE": "posix_collection_policies#1.1.0"
                            },
                            "public": True,
                            "require_mfa": False,
                            "storage_gateway_id": storage_gateway_id,
                            "tlsftp_url": "tlsftp://foo.abc.xyz.data.globus.org:443",
                        }
                    ],
                    "detail": "success",
                    "has_next_page": False,
                    "http_response_code": 200,
                },
                "metadata": {
                    "collection_id": collection_id,
                    "domain": domain,
                    "storage_gateway_id": storage_gateway_id,
                },
            }
        },
    )

    register_response_set(
        "cli.collection_create_mapped.get_endpoint",
        {
            "default": {
                "service": "transfer",
                "path": f"/v0.10/endpoint/{endpoint_id}",
                "method": "GET",
                "json": {
                    "DATA": [
                        {"DATA_TYPE": "server", "hostname": "abc.xyz.data.globus.org"}
                    ],
                    "DATA_TYPE": "endpoint",
                    "canonical_name": f"{endpoint_id}#{endpoint_id}",
                    "description": "example gcsv5 endpoint",
                    "display_name": "Happy Fun Endpoint",
                    "entity_type": "GCSv5_endpoint",
                    "gcs_manager_url": "https://abc.xyz.data.globus.org",
                    "gcs_version": "5.4.71",
                    "id": endpoint_id,
                    "is_globus_connect": False,
                    "non_functional": True,
                    "owner_id": endpoint_id,
                    "owner_string": f"{endpoint_id}@clients.auth.globus.org",
                    "subscription_id": None,
                },
                "metadata": {"endpoint_id": endpoint_id},
            }
        },
    )


@pytest.mark.parametrize(
    "only_one_storage_gateway, implicit_storage_gateway",
    (
        (False, False),
        (True, False),
        (True, True),
    ),
)
def test_mapped_collection_create(
    run_line,
    add_gcs_login,
    only_one_storage_gateway,
    implicit_storage_gateway,
    get_identities_mocker,
    identity_info,
):
    load_response(
        "cli.collection_create_mapped.storage_gateway_list",
        case="default" if only_one_storage_gateway else "multiple",
    )
    gcs_meta = load_response("cli.collection_create_mapped.get_endpoint").metadata
    create_meta = load_response(
        "cli.collection_create_mapped.mapped_collection_create"
    ).metadata
    get_identities_mocker.configure_one(**identity_info)

    owner_username = identity_info["username"]
    epid = gcs_meta["endpoint_id"]

    cmd = ["globus", "gcs", "collection", "create", "mapped", epid, "/"]
    if not implicit_storage_gateway:
        cmd.extend(["--storage-gateway-id", create_meta["storage_gateway_id"]])

    add_gcs_login(epid)
    run_line(
        cmd,
        search_stdout=[
            ("Storage Gateway ID", create_meta["storage_gateway_id"]),
            ("Owner", owner_username),
        ],
    )


def test_mapped_collection_create_fails_on_multiple_storage_gateways_unspecified(
    run_line, add_gcs_login
):
    load_response("cli.collection_create_mapped.storage_gateway_list", case="multiple")
    gcs_meta = load_response("cli.collection_create_mapped.get_endpoint").metadata
    epid = gcs_meta["endpoint_id"]

    add_gcs_login(epid)
    run_line(
        f"globus gcs collection create mapped {epid} /",
        assert_exit_code=2,
        search_stderr="This endpoint has multiple storage gateways.",
    )


def test_mapped_collection_create_fails_no_storage_gateways(run_line, add_gcs_login):
    load_response("cli.collection_create_mapped.storage_gateway_list", case="empty")
    gcs_meta = load_response("cli.collection_create_mapped.get_endpoint").metadata
    epid = gcs_meta["endpoint_id"]

    add_gcs_login(epid)
    run_line(
        f"globus gcs collection create mapped {epid} /",
        assert_exit_code=2,
        search_stderr="This endpoint does not have any storage gateways.",
    )


def test_mapped_collection_create_invalid_sharing_restrict_paths(run_line):
    run_line(
        (
            f"globus gcs collection create mapped {uuid.uuid4()} / "
            "--sharing-restrict-paths 0"
        ),
        assert_exit_code=2,
        search_stderr="--sharing-restrict-paths must be a JSON object",
    )


@pytest.mark.parametrize(
    "add_opts",
    (
        ["--google-project-id", "fooid"],
        ["--posix-sharing-group-allow", "foo", "--posix-sharing-group-deny", "bar"],
        [
            "--posix-staging-sharing-group-allow",
            "foo",
            "--posix-staging-sharing-group-deny",
            "bar",
        ],
    ),
)
def test_mapped_collection_create_accepts_various_policy_options(
    run_line,
    add_gcs_login,
    add_opts,
    get_identities_mocker,
    identity_info,
):
    load_response("cli.collection_create_mapped.storage_gateway_list")
    gcs_meta = load_response("cli.collection_create_mapped.get_endpoint").metadata
    create_meta = load_response(
        "cli.collection_create_mapped.mapped_collection_create"
    ).metadata
    get_identities_mocker.configure_one(**identity_info)

    owner_username = identity_info["username"]
    epid = gcs_meta["endpoint_id"]

    cmd = ["globus", "gcs", "collection", "create", "mapped", epid, "/"] + add_opts

    add_gcs_login(epid)
    run_line(
        cmd,
        search_stdout=[
            ("Storage Gateway ID", create_meta["storage_gateway_id"]),
            ("Owner", owner_username),
        ],
    )


@pytest.mark.parametrize(
    "add_opts",
    (
        pytest.param(
            ["--google-project-id", "fooid", "--posix-sharing-group-allow", "foo"],
            id="google+posix",
        ),
        pytest.param(
            [
                "--google-project-id",
                "fooid",
                "--posix-staging-sharing-group-allow",
                "foo",
            ],
            id="google+posix-staging",
        ),
        pytest.param(
            [
                "--posix-sharing-group-allow",
                "foo",
                "--posix-staging-sharing-group-allow",
                "foo",
            ],
            id="posix+posix-staging",
        ),
        pytest.param(
            [
                "--google-project-id",
                "fooid",
                "--posix-sharing-group-deny",
                "foo",
                "--posix-staging-sharing-group-deny",
                "foo",
            ],
            id="google+posix+posix-staging",
        ),
        pytest.param(
            ["--google-project-id", "", "--posix-sharing-group-allow", ""],
            id="google-emptystr+posix-emptystr",
        ),
    ),
)
def test_mapped_collection_create_rejects_incompatible_policy_options_as_mutex(
    run_line, add_gcs_login, add_opts
):
    load_response("cli.collection_create_mapped.storage_gateway_list")
    gcs_meta = load_response("cli.collection_create_mapped.get_endpoint").metadata

    epid = gcs_meta["endpoint_id"]

    cmd = ["globus", "gcs", "collection", "create", "mapped", epid, "/"] + add_opts

    add_gcs_login(epid)
    run_line(
        cmd,
        assert_exit_code=2,
        search_stderr=re.escape(
            "--google-project-id, "
            "--posix-sharing-group-allow/--posix-sharing-group-deny, and "
            "--posix-staging-sharing-group-allow/"
            "--posix-staging-sharing-group-deny "
            "are mutually exclusive"
        ),
    )
