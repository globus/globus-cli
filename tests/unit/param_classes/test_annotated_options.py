import pytest

from globus_cli.parsing import AnnotatedOption


def test_annotated_option_defaults_to_no_explicit_annotation():
    opt = AnnotatedOption(("--foo",))
    assert not opt.has_explicit_annotation()


def test_annotated_option_can_have_explicit_annotation():
    opt = AnnotatedOption(("--foo",), type_annotation=str)
    assert opt.has_explicit_annotation()


def test_annotated_option_returns_annotation_if_present():
    opt = AnnotatedOption(("--foo",), type_annotation=str)
    assert opt.type_annotation is str


def test_annotated_option_errors_if_nonexistent_annotation_is_accessed():
    opt = AnnotatedOption(("--foo",))
    with pytest.raises(ValueError, match="cannot get annotation"):
        opt.type_annotation
