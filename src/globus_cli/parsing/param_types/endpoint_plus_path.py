from __future__ import annotations

import typing as t
import uuid

import click

from globus_cli._click_compat import shim_get_metavar

if t.TYPE_CHECKING:
    _EndpointPlusPathBase = click.ParamType[tuple[uuid.UUID, str | None]]
else:
    _EndpointPlusPathBase = click.ParamType


class EndpointPlusPath(_EndpointPlusPathBase):
    """
    Custom type for "<endpoint_id>:<path>"
    Supports path being required and path being optional.

    Always produces a Tuple.
    """

    name = "endpoint plus path"

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        # path requirement defaults to True, but can be tweaked by a kwarg
        self.path_required = kwargs.pop("path_required", True)

        super().__init__(*args, **kwargs)

    def get_type_annotation(self, param: click.Parameter) -> type:
        # this is a "<typing special form>" vs "type" issue, so type ignore for now
        # click-type-test has an issue for improving this, with details, see:
        #   https://github.com/sirosen/click-type-test/issues/14
        if self.path_required:
            return t.Tuple[uuid.UUID, str]  # type: ignore[return-value]
        else:
            return t.Tuple[uuid.UUID, t.Union[str, None]]  # type: ignore[return-value]

    @shim_get_metavar
    def get_metavar(self, param: click.Parameter, ctx: click.Context) -> str:
        """
        Default metavar for this instance of the type.
        """
        return self.metavar

    @property
    def metavar(self) -> str:
        """
        Metavar as a property, so that we can make it different if `path_required`.
        """
        if self.path_required:
            return "ENDPOINT_ID:PATH"
        else:
            return "ENDPOINT_ID[:PATH]"

    def convert(
        self,
        value: tuple[uuid.UUID, str | None] | str,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> tuple[uuid.UUID, str | None]:
        """
        ParamType.convert() is the actual processing method that takes a
        provided parameter and parses it.
        """
        # passthrough conditions: None or already processed
        if isinstance(value, tuple):
            return value

        # split the value on the first colon, leave the rest intact
        splitval = value.split(":", 1)
        # first element is the endpoint_id
        # NOTE: for some reason, mypy thinks `click.UUID()` can return `None`, but that
        #       does not match its annotation
        endpoint_id: uuid.UUID = click.UUID(splitval[0])  # type: ignore[assignment]

        # get the second element, defaulting to `None` if there was no colon in
        # the original value
        try:
            path = splitval[1]
        except IndexError:
            path = None
        # coerce path="" to path=None
        # means that we treat "endpoint_id" and "endpoint_id:" equivalently
        path = path or None

        if path is None and self.path_required:
            self.fail("The path component is required", param=param)

        return (endpoint_id, path)


ENDPOINT_PLUS_OPTPATH = EndpointPlusPath(path_required=False)
ENDPOINT_PLUS_REQPATH = EndpointPlusPath(path_required=True)
