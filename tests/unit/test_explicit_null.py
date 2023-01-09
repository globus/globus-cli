from globus_cli.constants import EXPLICIT_NULL, ExplicitNullType


def test_explicit_null_object_is_falsy():
    assert bool(EXPLICIT_NULL) is False


def test_explicit_null_object_matches_type():
    assert isinstance(EXPLICIT_NULL, ExplicitNullType)


def test_explicit_null_stringify():
    assert str(EXPLICIT_NULL) == "null"


def test_nullify():
    assert ExplicitNullType.nullify(EXPLICIT_NULL) is None
    assert ExplicitNullType.nullify(None) is None
    assert ExplicitNullType.nullify(False) is False
    assert ExplicitNullType.nullify("foo") == "foo"


def test_nullify_dict():
    assert ExplicitNullType.nullify_dict({}) == {}
    assert ExplicitNullType.nullify_dict({"k": "v"}) == {"k": "v"}
    assert ExplicitNullType.nullify_dict({"k": None}) == {}
    assert ExplicitNullType.nullify_dict({"k": EXPLICIT_NULL}) == {"k": None}
    assert ExplicitNullType.nullify_dict({"k1": None, "k2": EXPLICIT_NULL}) == {
        "k2": None
    }
    assert ExplicitNullType.nullify_dict(
        {"k1": None, "k2": EXPLICIT_NULL, "k3": "v"}
    ) == {"k2": None, "k3": "v"}
