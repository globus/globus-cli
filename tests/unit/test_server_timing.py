import collections

import pytest

from globus_cli.termio.server_timing import (
    Draft2017Parser,
    Metric,
    ServerTimingParseError,
    render_metrics_onscreen,
)

terminal_dimensions = collections.namedtuple(
    "terminal_dimensions", ("columns", "lines")
)


def fake_get_terminal_size(fallback):
    return terminal_dimensions(20, 10)


@pytest.mark.parametrize(
    "metricstr, expect",
    (
        ("a=1", Metric(name="a", duration=1.0)),
        (
            'a=1; "complex desc"',
            Metric(name="a", duration=1.0, description="complex desc"),
        ),
        (
            "some-str",
            Metric(name="some-str"),
        ),
        (
            'some-str; "with a description"',
            Metric(name="some-str", description="with a description"),
        ),
        (
            'some-str=52.4; "with a description"',
            Metric(name="some-str", description="with a description", duration=52.4),
        ),
    ),
)
def test_draft2017_parse_of_single_metric(metricstr, expect):
    parser = Draft2017Parser()
    assert parser.parse_single_metric(metricstr) == expect


@pytest.mark.parametrize("metricstr", ("a; b; c", "", "a=foo"))
def test_draft2017_parse_single_metric_errors(metricstr):
    parser = Draft2017Parser()
    with pytest.raises(ServerTimingParseError):
        parser.parse_single_metric(metricstr)


@pytest.mark.parametrize(
    "metricstr, expect",
    (
        (
            "a=1, b=2.2",
            [
                Metric(name="a", duration=1.0),
                Metric(name="b", duration=2.2),
            ],
        ),
        (
            'a=1, b, c=2.2; "callout"',
            [
                Metric(name="a", duration=1.0),
                Metric(name="b"),
                Metric(name="c", duration=2.2, description="callout"),
            ],
        ),
        (
            ' a = 1 , b  ,c=2.2;"callout"   ',
            [
                Metric(name="a", duration=1.0),
                Metric(name="b"),
                Metric(name="c", duration=2.2, description="callout"),
            ],
        ),
    ),
)
def test_draft2017_parse_header_success(metricstr, expect):
    parser = Draft2017Parser()
    assert parser.parse_metric_header(metricstr) == expect


@pytest.mark.parametrize(
    "metricstr, expect_on_success",
    (
        (
            "a=1, ,b=2.2",
            [
                Metric(name="a", duration=1.0),
                Metric(name="b", duration=2.2),
            ],
        ),
        (
            'a=1, ;b, c=2.2; "callout"',
            [
                Metric(name="a", duration=1.0),
                Metric(name="c", duration=2.2, description="callout"),
            ],
        ),
    ),
)
@pytest.mark.parametrize("skip_errors", (True, False))
def test_draft2017_parse_header_errors(metricstr, expect_on_success, skip_errors):
    parser = Draft2017Parser()
    if skip_errors:
        assert (
            parser.parse_metric_header(metricstr, skip_errors=True) == expect_on_success
        )
    else:
        with pytest.raises(ServerTimingParseError):
            parser.parse_metric_header(metricstr, skip_errors=False)


def test_render_server_timing(capsys, monkeypatch):
    monkeypatch.setattr("shutil.get_terminal_size", fake_get_terminal_size)

    data = 'a=1, b, c=2.2; "callout"'
    parser = Draft2017Parser()
    metrics = parser.parse_metric_header(data)

    assert capsys.readouterr().err == ""
    render_metrics_onscreen(metrics)
    assert capsys.readouterr().err == ("""\
Server Timing Info
+------------------+
| a=1.0.......#    |
| callout=2.2.#### |
+------------------+
""")
