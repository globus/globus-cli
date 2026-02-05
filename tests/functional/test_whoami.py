import textwrap


def test_singular_whoami(run_line, userinfo_mocker):
    meta = userinfo_mocker.configure_unlinked().metadata
    result = run_line("globus whoami")
    assert result.output == f"{meta['username']}\n"


def test_verbose(run_line, userinfo_mocker):
    """
    Confirms --verbose includes Name, Email, and ID fields.
    """
    meta = userinfo_mocker.configure_unlinked().metadata

    result = run_line("globus whoami --verbose")
    for field in ["Username", "Name", "Email", "ID"]:
        assert field in result.output
    for field in ["username", "name", "email", "sub"]:
        assert meta[field] in result.output


def test_linked_identities(run_line, userinfo_mocker):
    """
    Confirms --linked-identities sees foo2.
    """
    usernames = ["aragorn@gondor.middleearth", "strider@wilds.middleearth"]
    userinfo_mocker.configure(
        {"username": usernames[0]},
        [{"username": usernames[1]}],
    )

    result = run_line("globus whoami --linked-identities")
    assert result.output == textwrap.dedent(f"""\
        {usernames[0]}
        {usernames[1]}
        """)
    for name in usernames:
        assert name in result.output


def test_verbose_linked_identities(run_line, userinfo_mocker):
    """
    Confirms combining --verbose and --linked-identities has expected
    values present for the whole identity set.
    """
    usernames = ["aragorn@gondor.middleearth", "strider@wilds.middleearth"]
    meta = userinfo_mocker.configure(
        {"username": usernames[0]},
        [{"username": usernames[0]}, {"username": usernames[1]}],
    ).metadata
    identity_set = meta["identity_set"]

    result = run_line("globus whoami --linked-identities -v")

    for field in ["Username", "Name", "Email", "ID"]:
        assert field in result.output
    for identity_doc in identity_set:
        for field in ["username", "name", "email", "sub"]:
            assert identity_doc[field] in result.output
