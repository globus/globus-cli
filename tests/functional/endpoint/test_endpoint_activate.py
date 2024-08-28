import uuid


def test_endpoint_activate_warns_of_removal(run_line):
    epid = str(uuid.UUID(int=1))
    command = [
        "globus",
        "endpoint",
        "activate",
        "--web",
        "--no-browser",
        "--force",
        "--no-autoactivate",
        epid,
    ]
    result = run_line(command)
    assert "removed in a future release" in result.stderr
