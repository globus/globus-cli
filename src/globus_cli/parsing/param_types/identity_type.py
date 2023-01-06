import base64
import uuid
from collections import namedtuple

import click

from .annotated_param import AnnotatedParamType

ParsedIdentity = namedtuple("ParsedIdentity", ["value", "idtype"])


class _B32DecodeError(ValueError):
    """custom exception type"""


def _b32decode(v):
    # should start with "u_"
    if not v.startswith("u_"):
        raise _B32DecodeError("should start with 'u_'")
    v = v[2:]
    # wrong length
    if len(v) != 26:
        raise _B32DecodeError("wrong length")

    # append padding and uppercase so that b32decode will work
    v = v.upper() + (6 * "=")

    # try to decode
    try:
        return str(uuid.UUID(bytes=base64.b32decode(v)))
    # if it fails, then it can't be a b32-encoded identity
    except ValueError:
        raise _B32DecodeError("decode and load as UUID failed")


class IdentityType(AnnotatedParamType):
    """
    Parameter type for handling identities. By default, just allows usernames or
    identity IDs. With options, it can be set to allow domain names as an "identity"
    type, or to allow the use of b32-encoded usernames.

    Returns a named tuple containing
      (value, idtype)
    where "value" is whatever unparsed value we received, and "idtype" is one of
    {"identity", "username", "domain"}
    """

    name = "IDENTITY"

    def __init__(self, allow_domains=False, allow_b32_usernames=False):
        self.allow_domains = allow_domains
        self.allow_b32_usernames = allow_b32_usernames

    def get_type_annotation(self, param: click.Parameter) -> type:
        return ParsedIdentity

    def convert(self, value, param, ctx):
        # uuid format -> identity
        try:
            uuid.UUID(value)
            return ParsedIdentity(value, "identity")
        except ValueError:
            pass

        # "foo@bar" -> username
        if "@" in value:
            return ParsedIdentity(value, "username")

        # if allowed, try a b32 decode at this point
        # if it fails, fallthrough
        if self.allow_b32_usernames:
            try:
                return ParsedIdentity(_b32decode(value), "identity")
            except _B32DecodeError:
                pass

        # if domains are allowed, reason that the identity must be a domain by process
        # of elimination
        #
        # allows "foo.bar", "net", "com", "abc.def.org", etc
        if self.allow_domains:
            return ParsedIdentity(value, "domain")

        self.fail(f"'{value}' does not appear to be a valid identity", param=param)

    def get_metavar(self, param):
        return self.metavar

    @property
    def metavar(self):
        if self.allow_domains:
            return "IDENTITY_OR_DOMAIN"
        else:
            return "IDENTITY"
