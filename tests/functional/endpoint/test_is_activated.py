import uuid


def test_endpoint_is_activated_warns_of_removal(run_line):
    epid = str(uuid.UUID(int=1))
    command = ["globus", "endpoint", "is-activated", "--until", "3600", epid]
    result = run_line(command)
    assert "removed in a future release" in result.stderr
