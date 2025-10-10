import json

from globus_sdk.testing import load_response


def test_show_run_definition(run_line, add_flow_login):
    # Load the response mock and extract critical metadata.
    response = load_response("flows.get_run_definition")
    run_id = response.metadata["run_id"]

    # Construct the command line.
    cli = f"globus flows run show-definition {run_id}"
    result = run_line(cli)

    # Verify the output is JSON.
    parsed_output = json.loads(result.stdout)

    # Verify the keys have not been sorted.
    assert list(parsed_output.keys()) == list(response.responses[0].json.keys())
