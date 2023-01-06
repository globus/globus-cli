import uuid

import click

from .annotated_param import AnnotatedParamType


class EndpointPlusPath(AnnotatedParamType):
    """
    Custom type for "<endpoint_id>:<path>"
    Supports path being required and path being optional.

    Always produces a Tuple.
    """

    name = "endpoint plus path"

    def __init__(self, *args, **kwargs):
        # path requirement defaults to True, but can be tweaked by a kwarg
        self.path_required = kwargs.pop("path_required", True)

        super().__init__(*args, **kwargs)

    def get_type_annotation(self, param: click.Parameter) -> type:
        if self.path_required:
            return tuple[uuid.UUID, str]
        else:
            return tuple[uuid.UUID, str | None]

    def get_metavar(self, param):
        """
        Default metavar for this instance of the type.
        """
        return self.metavar

    @property
    def metavar(self):
        """
        Metavar as a property, so that we can make it different if `path_required`
        """
        if self.path_required:
            return "ENDPOINT_ID:PATH"
        else:
            return "ENDPOINT_ID[:PATH]"

    def convert(self, value, param, ctx):
        """
        ParamType.convert() is the actual processing method that takes a
        provided parameter and parses it.
        """
        # passthrough conditions: None or already processed
        if value is None or isinstance(value, tuple):
            return value

        # split the value on the first colon, leave the rest intact
        splitval = value.split(":", 1)
        # first element is the endpoint_id
        endpoint_id = click.UUID(splitval[0])

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
