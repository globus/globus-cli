import uuid

import pytest
from globus_sdk.testing import RegisteredResponse, load_response_set


@pytest.mark.parametrize("ep_type", ["personal", "share", "server"])
def test_show_works(run_line, ep_type):
    meta = load_response_set("cli.endpoint_operations").metadata
    if ep_type == "personal":
        epid = meta["gcp_endpoint_id"]
    elif ep_type == "share":
        epid = meta["share_id"]
    else:
        epid = meta["endpoint_id"]

    result = run_line(f"globus endpoint show {epid}")

    assert "Display Name:" in result.output
    assert epid in result.output


def test_show_long_description(run_line):
    epid = str(uuid.uuid4())
    repeated_line = "AAAAAAAAAAAAH"

    RegisteredResponse(
        service="transfer",
        path=f"/v0.10/endpoint/{epid}",
        json={
            "id": epid,
            "display_name": "EndlessScreaming",
            "owner_string": "cthulhu@r'lyeh",
            "description": f"{repeated_line}\n" * 1000,
            "shareable": False,
            "keywords": "endless,scream,lovecraft,cthonic",
            "info_link": None,
            "Contact E-mail": "aaaaaaaah",
            "organization": "Great Old Ones",
            "department": None,
            "contact_info": None,
            "public": True,
            "default_directory": "/~/",
            "force_encryption": False,
            "subscription_id": None,
            "canonical_name": "cthulhu#endlessscreaming",
            "local_user_info_available": False,
            "is_globus_connect": False,
        },
    ).add()

    result = run_line(f"globus endpoint show {epid}")

    # output must be length limited (truncated)
    # this can be asserted by the fact that the full description is longer than
    # the total output length
    assert len(result.output) < 3000

    # find the lines of description in the output
    output_lines = result.output.splitlines()
    desc_lineno = -1
    for i in range(len(output_lines)):
        if output_lines[i].startswith("Description:"):
            desc_lineno = i
            break
    else:
        pytest.fail("did not find Description in output")

    desc_line_end = desc_lineno + 1
    for i in range(desc_line_end, len(output_lines)):
        if output_lines[i].startswith(" "):
            continue
        else:
            desc_line_end = i
            break
    else:
        # Description could move to the end of output in the future, in which case we'll
        # never find a "next field", in which case, `-1` for good ranges
        desc_line_end = -1

    description_lines = output_lines[desc_lineno:desc_line_end]

    # there should be exactly 6 lines of relevant output
    assert len(description_lines) == 6

    # the first line has the name of the field and the first line of text
    lead_line = description_lines[0]
    assert lead_line.startswith("Description:")
    lead_value = lead_line.partition(":")[2].strip()
    assert lead_value == repeated_line

    # all remaining lines are just the repeated string
    # except for the last one, which gets a '...'
    for x in description_lines[1:-1]:
        assert x.strip() == repeated_line

    assert description_lines[-1].strip() == "..."


# confirm that this *does not* error:
# showing a GCSv5 host needs to be supported for show (unlike update, delete, etc)
def test_show_on_gcsv5_endpoint(run_line):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["endpoint_id"]

    result = run_line(f"globus endpoint show {epid}")
    assert "Display Name:" in result.output
    assert epid in result.output


def test_show_on_gcsv5_collection(run_line):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["mapped_collection_id"]

    result = run_line(f"globus endpoint show {epid}", assert_exit_code=3)
    assert (
        f"Expected {epid} to be an endpoint ID.\n"
        "Instead, found it was of type 'Globus Connect Server v5 Mapped Collection'."
    ) in result.stderr
    assert (
        "Please run the following command instead:\n\n"
        f"    globus gcs collection show {epid}"
    ) in result.stderr


def test_show_on_gcsv5_collection_skip_check(run_line):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["mapped_collection_id"]

    result = run_line(f"globus endpoint show --skip-endpoint-type-check {epid}")
    assert "Display Name:" in result.output
    assert epid in result.output
