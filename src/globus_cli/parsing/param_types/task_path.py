import click

from .annotated_param import AnnotatedParamType


def _normpath(path):
    """
    Globus Transfer-specific normalization, based on a careful reading of the stdlib
    posixpath implementation:
      https://github.com/python/cpython/blob/ea0f7aa47c5d2e58dc99314508172f0523e144c6/Lib/posixpath.py#L338

    this must be done without using os.path.normpath to be compatible with CLI calls
    from Windows systems

    Transfer requires forward slashes, even when communicating with Windows systems, so
    we must handle these strings appropriately.
    Note that this does not preserve leading slashes in the same way as python's
    posixpath module -- it's not clear how Transfer would treat such paths and
    non-obvious that we need to allow such usage

    Also, unlike normpath, we want to preserve trailing slashes because they may be
    required
    """
    initial_slash = 1 if path.startswith("/") else 0
    trailing_slash = 1 if path.endswith("/") and path != "/" else 0
    parts = path.split("/")
    new_parts = []
    for part in parts:
        if part in ("", "."):
            continue
        # either not adding a ".." OR chaining together multiple ".."s
        # OR working with a non-absolute path that starts with ".."
        if (
            part != ".."
            or (new_parts and new_parts[-1] == "..")
            or (not initial_slash and not new_parts)
        ):
            new_parts.append(part)
        elif new_parts:  # adding a ".." to a path which isn't already ending in one
            new_parts.pop()

    return ("/" * initial_slash) + "/".join(new_parts) + ("/" * trailing_slash)


def _pathjoin(a, b):
    """
    POSIX-like path join for Globus Transfer paths

    As with _normpath above, this is meant to behave correctly even on Windows systems
    """
    if not b:  # given "" as a file path
        return a
    elif b.startswith("/"):  # a path starting with / is absolute
        return b

    if a.endswith("/"):
        return a + b
    else:
        return a + "/" + b


class TaskPath(AnnotatedParamType):
    def __init__(
        self, base_dir=None, coerce_to_dir=False, normalize=True, require_absolute=False
    ):
        """
        Task Paths are paths for passing into Transfer or Delete tasks.
        They're only slightly more than string types: they can join themselves
        with a base dir path, and they can coerce themselves to the dir format
        by appending a trailing slash if it's absent.

        For us to toggle and talk about behaviors as necessary, normalization
        is an option that defaults to True.
        Also can enforce that the path is absolute.
        """
        self.base_dir = base_dir
        self.coerce_to_dir = coerce_to_dir
        self.normalize = normalize
        self.require_absolute = require_absolute

        # the "real value" of this path holder
        self.path = None
        # the original path, as consumed before processing
        self.orig_path = None

    def get_type_annotation(self, param: click.Parameter) -> type:
        return TaskPath

    def convert(self, value, param, ctx):
        if ctx.resilient_parsing:
            return
        if isinstance(value, TaskPath):
            return value

        self.orig_path = self.path = value

        if self.base_dir:
            self.path = _pathjoin(self.base_dir, self.path)
        if self.coerce_to_dir and not self.path.endswith("/"):
            self.path += "/"
        if self.normalize:
            self.path = _normpath(self.path)

        if self.require_absolute and not (
            self.path.startswith("/") or self.path.startswith("~")
        ):
            self.fail(
                f"{self.path} is not absolute (abspath required)",
                param=param,
                ctx=ctx,
            )

        return self

    def __repr__(self):
        return "TaskPath({})".format(
            ",".join(
                f"{name}={getattr(self, name)}"
                for name in (
                    "base_dir",
                    "coerce_to_dir",
                    "normalize",
                    "path",
                    "orig_path",
                )
            )
        )

    def __str__(self):
        return str(self.path)
