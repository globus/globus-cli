from globus_sdk._testing import RegisteredResponse, load_response


def test_resume_run_text_output(run_line, add_flow_login):
    # get fields for resume_run
    response = load_response("flows.resume_run")
    meta = response.metadata
    response_payload = response.json
    flow_id = meta["flow_id"]
    run_id = meta["run_id"]
    tags = response_payload["tags"]
    label = response_payload["label"]
    status = response_payload["status"]
    flow_title = response_payload["flow_title"]

    # setup a GET /runs/{run_id} mock
    # it only needs to return a matching flow_id
    # (NB: the mock for 'flows.get_run' does not have the same run_id)
    load_response(
        RegisteredResponse(
            service="flows",
            method="get",
            path=f"/runs/{run_id}",
            json={
                "flow_id": flow_id,
            },
        )
    )

    # setup the login mock for that flow_id as well, so that we can
    # get a SpecificFlowClient for this flow
    add_flow_login(flow_id)

    run_line(
        ["globus", "flows", "run", "resume", run_id],
        search_stdout=[
            ("Flow ID", flow_id),
            ("Run ID", run_id),
            ("Run Tags", ",".join(tags)),
            ("Run Label", label),
            ("Status", status),
            ("Flow Title", flow_title),
        ],
    )
