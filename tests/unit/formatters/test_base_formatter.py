import pytest

from globus_cli.termio import formatters


def test_base_formatter_does_not_pass_null_by_default():
    # a formatter which forcibly rejects None
    class FormatterRejectingNulls(formatters.FieldFormatter):
        def parse(self, value):
            assert value is not None
            return value

        def render(self, value):
            assert value is not None
            return ""

    # pass that formatter None
    fmt = FormatterRejectingNulls()
    result = fmt.format(None)
    # the base formatter should intercept the None and render it as a string
    assert result == "None"


def test_base_formatter_will_pass_null_if_asked():
    parse_was_called = False
    render_was_called = False

    class FormatterSettingNonlocals(formatters.FieldFormatter):
        # set this value to ensure that None gets passed through
        parse_null_values = True

        def parse(self, value):
            nonlocal parse_was_called
            parse_was_called = True
            assert value is None
            return value

        def render(self, value):
            nonlocal render_was_called
            render_was_called = True
            assert value is None
            return ""

    # pass that formatter None and make sure it side-effects as expected
    fmt = FormatterSettingNonlocals()
    result = fmt.format(None)
    assert parse_was_called
    assert render_was_called
    assert result == ""


def test_base_formatter_handles_value_error_in_parse():
    class CannotParseFormatter(formatters.FieldFormatter):
        def parse(self, value):
            raise ValueError("uh-oh")

        def render(self, value):
            return ""

    fmt = CannotParseFormatter()
    with pytest.warns(formatters.FormattingFailedWarning):
        result = fmt.format("test")
    assert result == "test"


def test_base_formatter_handles_value_error_in_render():
    class CannotRenderFormatter(formatters.FieldFormatter):
        def parse(self, value):
            return value

        def render(self, value):
            raise ValueError("uh-oh")

    fmt = CannotRenderFormatter()
    with pytest.warns(formatters.FormattingFailedWarning):
        result = fmt.format("test")
    assert result == "test"
