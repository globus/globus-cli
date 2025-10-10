from __future__ import annotations

import re

from globus_sdk.testing import load_response


def _urn_to_id(s: str) -> str | None:
    if s.startswith("urn:globus:auth:identity:"):
        return s.split(":")[-1]
    return None


def test_show_flow_text_output(run_line, get_identities_mocker):
    get_response = load_response("flows.get_flow")
    flow_id = get_response.metadata["flow_id"]
    keywords = get_response.json["keywords"]

    aragorn_id = _urn_to_id(get_response.json["run_managers"][0])
    gandalf_id = _urn_to_id(get_response.json["run_monitors"][0])

    legolas_id = _urn_to_id(get_response.json["flow_owner"])
    viewer_identity_ids = [
        x
        for x in (_urn_to_id(v) for v in get_response.json["flow_viewers"])
        if x is not None
    ]
    gimli_id = viewer_identity_ids[0]
    generic_dwarves = viewer_identity_ids[1:]

    expect_owner = "legolas@rivendell.middleearth"
    expect_viewers = "gimli@rivendell.middleearth"
    expect_starters = "frodo@rivendell.middleearth"
    expect_run_managers = "aragorn@rivendell.middleearth"
    expect_run_monitors = "gandalf@rivendell.middleearth"

    starter_identity_ids = [
        x
        for x in (_urn_to_id(v) for v in get_response.json["flow_starters"])
        if x is not None
    ]
    frodo_id = starter_identity_ids[0]
    generic_hobbits = starter_identity_ids[1:]

    get_identities_mocker.configure(
        [
            {
                "username": "legolas@rivendell.middleearth",
                "name": "Orlando Bloom",
                "id": legolas_id,
            },
            {
                "username": "gimli@rivendell.middleearth",
                "name": "John Rhys-Davies",
                "id": gimli_id,
            },
            {
                "username": "frodo@rivendell.middleearth",
                "name": "Elijah Wood",
                "id": frodo_id,
            },
            {
                "username": "aragorn@rivendell.middleearth",
                "name": "Viggo Mortensen",
                "id": aragorn_id,
            },
            {
                "username": "gandalf@rivendell.middleearth",
                "name": "Ian McKellen",
                "id": gandalf_id,
            },
        ]
        + [
            {
                "username": "genericdwarf{i}@rivendell.middleearth",
                "name": "Generic LOTR Character",
                "id": identity_id,
            }
            for i, identity_id in enumerate(generic_dwarves)
        ]
        + [
            {
                "username": "generichobbit{i}@rivendell.middleearth",
                "name": "Generic LOTR Character",
                "id": identity_id,
            }
            for i, identity_id in enumerate(generic_hobbits)
        ]
    )

    result = run_line(f"globus flows show {flow_id}")
    # all fields present
    for fieldname in (
        "Flow ID",
        "Title",
        "Keywords",
        "Owner",
        "Created At",
        "Updated At",
        "Administrators",
        "Viewers",
        "Starters",
        "Run Managers",
        "Run Monitors",
    ):
        assert fieldname in result.output
    # array formatters worked as expected
    assert (
        re.search(r"Keywords:\s+" + re.escape(",".join(keywords)), result.output)
        is not None
    )
    assert re.search(r"Owner:\s+" + re.escape(expect_owner), result.output) is not None
    assert (
        re.search(r"Viewers:\s+" + re.escape(f"public,{expect_viewers}"), result.output)
        is not None
    )
    assert (
        re.search(
            r"Starters:\s+all_authenticated_users," + re.escape(expect_starters),
            result.output,
        )
        is not None
    )
    assert (
        re.search(r"Run Managers:\s+" + re.escape(expect_run_managers), result.output)
        is not None
    )
    assert (
        re.search(r"Run Monitors:\s+" + re.escape(expect_run_monitors), result.output)
        is not None
    )
