from globus_sdk.testing import load_response


def test_delete_flow_text_output(run_line, get_identities_mocker):
    delete_response = load_response("flows.delete_flow")
    flow_id = delete_response.metadata["flow_id"]
    user_meta = get_identities_mocker.configure_one(
        id=delete_response.json["flow_owner"].split(":")[-1]
    ).metadata

    result = run_line(
        f"globus flows delete {flow_id}",
        search_stdout=[
            ("Flow ID", flow_id),
            ("Owner", user_meta["username"]),
            ("Deleted", "True"),
        ],
    )
    # all other fields also present
    for fieldname in (
        "Title",
        "Created At",
        "Updated At",
    ):
        assert fieldname in result.output
