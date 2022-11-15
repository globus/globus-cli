"""
Endpointish, a dialect of Elvish spoken only within Globus.


The Endpointish is mostly an Endpoint document from the Transfer service, wrapped
with additional helpers and functionality.

Importantly, it is not meant to represent an Endpoint either in the sense of GCSv4 and
GCP nor in the sense of GCSv5. It represents a wrapped Endpoint document, with
introspection and other niceties.

Think of it as a TransferClient.get_endpoint call + a location to cache the result + any
decoration we might want for this.
"""
from .endpointish import Endpointish
from .entity_type import EntityType
from .errors import ExpectedCollectionError, ExpectedEndpointError, WrongEntityTypeError

__all__ = [
    "Endpointish",
    "WrongEntityTypeError",
    "ExpectedCollectionError",
    "ExpectedEndpointError",
    "EntityType",
]
