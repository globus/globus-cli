import pytest

from globus_cli.commands.endpoint.server.show import PortRangeFormatter
from globus_cli.termio import formatters


def test_normal_case():
    fmt = PortRangeFormatter()
    data = fmt.format(
        {
            "incoming_data_port_start": 50000,
            "incoming_data_port_end": 51000,
            "outgoing_data_port_start": 50000,
            "outgoing_data_port_end": 51000,
        }
    )
    assert data == "incoming 50000-51000, outgoing 50000-51000"


def test_unspecified_incoming():
    fmt = PortRangeFormatter()
    data = fmt.format(
        {
            "incoming_data_port_start": None,
            "incoming_data_port_end": None,
            "outgoing_data_port_start": 50000,
            "outgoing_data_port_end": 51000,
        }
    )
    assert data == "incoming unspecified, outgoing 50000-51000"


def test_unspecified_outgoing():
    fmt = PortRangeFormatter()
    data = fmt.format(
        {
            "incoming_data_port_start": 50000,
            "incoming_data_port_end": 51000,
            "outgoing_data_port_start": None,
            "outgoing_data_port_end": None,
        }
    )
    assert data == "incoming 50000-51000, outgoing unspecified"


def test_unspecified_by_absence():
    fmt = PortRangeFormatter()
    data = fmt.format({})
    assert data == "incoming unspecified, outgoing unspecified"


def test_all_unrestricted():
    fmt = PortRangeFormatter()
    data = fmt.format(
        {
            "incoming_data_port_start": 1024,
            "incoming_data_port_end": 65535,
            "outgoing_data_port_start": 1024,
            "outgoing_data_port_end": 65535,
        }
    )
    assert data == "incoming unrestricted, outgoing unrestricted"


def test_handles_string_with_warning():
    fmt = PortRangeFormatter()
    with pytest.warns(formatters.FormattingFailedWarning):
        data = fmt.format("80-443")
    assert data == "80-443"


def test_handles_non_int_values():
    fmt = PortRangeFormatter()
    doc = {
        "incoming_data_port_start": "50000",
        "incoming_data_port_end": "51000",
        "outgoing_data_port_start": "50000",
        "outgoing_data_port_end": "51000",
    }
    with pytest.warns(formatters.FormattingFailedWarning):
        data = fmt.format(doc)
    assert data == str(doc)


def test_handles_mismatched_unbounded_range():
    fmt = PortRangeFormatter()
    doc = {
        "incoming_data_port_start": None,
        "incoming_data_port_end": 51000,
    }
    with pytest.warns(formatters.FormattingFailedWarning):
        data = fmt.format(doc)
    assert data == str(doc)
