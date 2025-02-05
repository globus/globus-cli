from globus_cli.termio.terminal_info import (
    TERM_INFO,
    TerminalTextWrapper,
    VirtualTerminalInfo,
)


def test_terminal_info_indents():
    term_info = VirtualTerminalInfo()

    columns = term_info.columns
    with term_info.indented(4):
        assert term_info.columns == columns - 4
        with term_info.indented(4):
            assert term_info.columns == columns - 8
        assert term_info.columns == columns - 4
    assert term_info.columns == columns


def test_terminal_info_indentation_is_reset_on_exception():
    term_info = VirtualTerminalInfo()

    columns = term_info.columns
    try:
        with term_info.indented(4):
            assert term_info.columns == columns - 4
            raise ValueError("test")
    except ValueError:
        pass
    assert term_info.columns == columns


def test_terminal_text_wrapper_wraps_to_terminal():
    wrapper = TerminalTextWrapper()
    assert wrapper.width == TERM_INFO.columns

    a_line = "a" * wrapper.width
    assert wrapper.wrap(a_line) == [a_line]
    assert wrapper.wrap(a_line + "a") == [a_line, "a"]


def test_terminal_text_wrapper_respects_indentation():
    wrapper = TerminalTextWrapper()

    initial_width = TERM_INFO.columns
    assert wrapper.width == initial_width

    with TERM_INFO.indented(4):
        assert wrapper.width == initial_width - 4
