from globus_cli.termio.terminal_info import VirtualTerminalInfo


def test_terminal_info_indents():
    term_info = VirtualTerminalInfo()

    columns = term_info.columns
    with term_info.indented(4):
        assert term_info.columns == columns - 4
        with term_info.indented(4):
            assert term_info.columns == columns - 8
        assert term_info.columns == columns - 4
    assert term_info.columns == columns
