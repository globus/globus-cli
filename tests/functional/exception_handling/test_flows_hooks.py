import json

from globus_sdk.testing import RegisteredResponse


def test_flows_generic_hook_on_long_detail(run_line):
    RegisteredResponse(
        service="flows",
        path="/flow/validate",
        method="POST",
        status=422,
        json={
            "error": {
                "code": "FLOW_VALIDATION_FAILED",
                "detail": (
                    "An attempt was made to read data improperly during analysis. "
                    "A known constraint was violated in state y: "
                    "Attempted to access keys ['foo'] which are not a part of this "
                    "data. The valid keys are ['bar'] ; "
                    "in state 'y' reading data which originated at state "
                    "'x' (result) > $"
                ),
                "message": (
                    "Failed to analyze this flow. "
                    "Something went wrong during the traversal of the flow definition."
                ),
            },
            "debug_id": "afa9ddb9-2f0e-4e24-ba76-79352fef1d19",
        },
    ).add()

    inlined_flow = json.dumps(
        {
            "definition": {
                "StartAt": "x",
                "States": {
                    "x": {"Type": "Pass", "Result": {"bar": [0]}, "Next": "y"},
                    "y": {"Type": "Pass", "InputPath": "$.foo[0]", "End": True},
                },
            }
        }
    )
    result = run_line(
        f"globus api flows POST /flow/validate --body '{inlined_flow}'",
        assert_exit_code=1,
    )
    assert "A Flows API Error Occurred." in result.stderr
    assert "Failed to analyze this flow." in result.stderr
    # none of the lines are super long, right?
    for line in result.stderr.split("\n"):
        assert len(line) < 120


def test_flows_generic_hook_on_detail_array(run_line):
    RegisteredResponse(
        service="flows",
        path="/flow/validate",
        method="POST",
        status=422,
        json={
            "error": {
                "code": "FLOW_VALIDATION_FAILED",
                "detail": [
                    {
                        "loc": ["definition", "States", "y", "SecondsPath"],
                        "msg": (
                            "Improper access to data in this wait "
                            "state with expression: $.foo[0]"
                        ),
                        "type": "InvalidAccessPath",
                        "ctx": {"field_name": "SecondsPath"},
                    }
                ],
                "message": "This flow contains errors in 1 wait state.",
            },
            "debug_id": "7475b494-bfff-4aad-aa6b-9534b9721c65",
        },
    ).add()

    inlined_flow = json.dumps(
        {
            "definition": {
                "StartAt": "x",
                "States": {
                    "x": {"Type": "Pass", "Result": {"bar": [0]}, "Next": "y"},
                    "y": {"Type": "Wait", "SecondsPath": "$.foo[0]", "End": True},
                },
            }
        }
    )
    result = run_line(
        f"globus api flows POST /flow/validate --body '{inlined_flow}'",
        assert_exit_code=1,
    )
    assert "A Flows API Error Occurred." in result.stderr
    assert "This flow contains errors in 1 wait state." in result.stderr
    assert "detail:" in result.stderr
    assert (
        "InvalidAccessPath $.definition.States.y.SecondsPath: "
        "Improper access to data in this wait state with expression: $.foo[0]"
        in result.stderr
    )


def test_flows_validation_hook_on_single_error(run_line):
    RegisteredResponse(
        service="flows",
        path="/flow/validate",
        method="POST",
        status=422,
        json={
            "error": {
                "code": "UNPROCESSABLE_ENTITY",
                "detail": [
                    {
                        "loc": ["definition", "States", "hi"],
                        "msg": "Discriminator 'type' is missing in value",
                        "type": (
                            "value_error.discriminated_union.missing_discriminator"
                        ),
                        "ctx": {"discriminator_key": "type"},
                    }
                ],
                "message": (
                    "1 validation error in body. "
                    "$.definition.States.hi: "
                    "Discriminator 'type' is missing in value"
                ),
            },
            "debug_id": "7bb1ddee-f41d-4e80-9bd7-fd16966e783b",
        },
    ).add()
    result = run_line(
        "globus api flows POST /flow/validate --body "
        '\'{"definition": {"StartAt": "hi", "States": {"hi": {}}}}\'',
        assert_exit_code=1,
    )
    assert "A Flows API Error Occurred." in result.stderr
    assert (
        "$.definition.States.hi: Discriminator 'type' is missing in value"
        in result.stderr
    )


def test_flows_validation_hook_on_multiple_errors(run_line):
    RegisteredResponse(
        service="flows",
        path="/flow/validate",
        method="POST",
        status=422,
        json={
            "error": {
                "code": "UNPROCESSABLE_ENTITY",
                "detail": [
                    {
                        "loc": ["definition"],
                        "msg": "none is not an allowed value",
                        "type": "type_error.none.not_allowed",
                    },
                    {
                        "loc": ["StartAt"],
                        "msg": "extra fields not permitted",
                        "type": "value_error.extra",
                    },
                ],
                "message": (
                    "2 validation errors in body. "
                    "$.definition: none is not an allowed value ; "
                    "$.StartAt: extra fields not permitted"
                ),
            },
            "debug_id": "fae137a7-9e4d-4009-aec2-efe71d02c509",
        },
    ).add()
    result = run_line(
        "globus api flows POST /flow/validate --body "
        '\'{"definition": null, "StartAt": "4tehlulz"}\'',
        assert_exit_code=1,
    )
    assert "A Flows API Error Occurred." in result.stderr
    assert "$.definition: none is not an allowed value" in result.stderr
    assert "$.StartAt: extra fields not permitted" in result.stderr


def test_flows_validation_hook_on_multiple_strange_errors(run_line):
    RegisteredResponse(
        service="flows",
        path="/frobulate",
        method="POST",
        status=422,
        # this is an error shape which does not meet our expectations
        # verify that we still get the message field, at the very least
        json={
            "error": {
                "code": "UNPROCESSABLE_ENTITY",
                "detail": [
                    {
                        "loc": ["a"],
                        "msg": "messageA",
                        "type": "typeA",
                    },
                    {
                        "loc": ["b"],
                        "msg": "messageB",
                        "type": "typeB",
                    },
                    # perhaps there's a special case where 'msg' or 'loc' is absent...
                    {"type": "kaboom!"},
                ],
                "message": "it went boom",
            },
            "debug_id": "fae137a7-9e4d-4009-aec2-efe71d02c509",
        },
    ).add()
    result = run_line(
        "globus api flows POST /frobulate --body '[]'", assert_exit_code=1
    )
    assert "A Flows API Error Occurred." in result.stderr
    assert "it went boom" in result.stderr
