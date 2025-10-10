import globus_sdk
import responses
from globus_sdk.testing import load_response_set


def test_endpoint_show(run_line, add_gcs_login):
    endpoint_id = load_response_set("cli.endpoint_introspect").metadata["endpoint_id"]
    load_response_set("cli.gcs_endpoint_operations")

    add_gcs_login(endpoint_id)

    resp = run_line(f"globus gcs endpoint show {endpoint_id}")

    assert endpoint_id in resp.stdout


def test_endpoint_show__normal_network_use_formatting(run_line, add_gcs_login):
    meta = load_response_set("cli.endpoint_introspect").metadata
    endpoint_id = meta["endpoint_id"]
    manager_url = meta["gcs_manager_url"]
    load_response_set("cli.gcs_endpoint_operations")

    add_gcs_login(endpoint_id)

    response = globus_sdk.GCSClient(manager_url).get_endpoint().full_data
    response["data"][0]["network_use"] = "normal"
    responses.replace("GET", f"{manager_url}/api/endpoint", json=response)

    resp = run_line(f"globus gcs endpoint show {endpoint_id}")

    assert _printed_table_val(resp.stdout, "Network Use") == "normal"
    assert _printed_table_val(resp.stdout, "Network Use (Concurrency)") == "normal"
    assert _printed_table_val(resp.stdout, "Network Use (Parallelism)") == "normal"


def _test_endpoint_show__custom_network_use_formatting(run_line, add_gcs_login):
    meta = load_response_set("cli.endpoint_introspect").metadata
    endpoint_id = meta["endpoint_id"]
    manager_url = meta["gcs_manager_url"]
    load_response_set("cli.gcs_endpoint_operations")

    add_gcs_login(endpoint_id)

    response = globus_sdk.GCSClient(manager_url).get_endpoint().full_data
    response["data"][0]["network_use"] = "custom"
    response["data"][0]["preferred_concurrency"] = 1
    response["data"][0]["max_concurrency"] = 2
    response["data"][0]["preferred_parallelism"] = 3
    response["data"][0]["max_parallelism"] = 4
    responses.replace("GET", f"{manager_url}/api/endpoint", json=response)

    resp = run_line(f"globus gcs endpoint show {endpoint_id}")

    assert _printed_table_val(resp.stdout, "Network Use") == "custom"
    actual_concurrency = _printed_table_val(resp.stdout, "Network Use (Concurrency)")
    assert actual_concurrency == "Preferred: 1, Max: 2"
    actual_parallelism = _printed_table_val(resp.stdout, "Network Use (Parallelism)")
    assert actual_parallelism == "Preferred: 3, Max: 4"


def _printed_table_val(stdout: str, key: str) -> str:
    prefix = f"{key}:"
    for line in stdout.splitlines():
        if line.startswith(prefix):
            return line.split(":")[1].strip()
