from __future__ import annotations

from enum import Enum, auto


class EndpointType(Enum):
    # endpoint / collection types
    GCP = auto()
    GCSV5_ENDPOINT = auto()
    GUEST_COLLECTION = auto()
    MAPPED_COLLECTION = auto()
    SHARE = auto()
    NON_GCSV5_ENDPOINT = auto()  # most likely GCSv4, but not necessarily

    @classmethod
    def collections(cls) -> tuple[EndpointType, ...]:
        return (cls.GUEST_COLLECTION, cls.MAPPED_COLLECTION)

    @classmethod
    def traditional_endpoints(cls) -> tuple[EndpointType, ...]:
        return (cls.GCP, cls.SHARE, cls.NON_GCSV5_ENDPOINT)

    @classmethod
    def non_collection_types(cls) -> tuple[EndpointType, ...]:
        return tuple(x for x in cls if x not in cls.collections())

    @classmethod
    def gcsv5_types(cls) -> tuple[EndpointType, ...]:
        return tuple(
            x for x in cls if (x is cls.GCSV5_ENDPOINT or x in cls.collections())
        )

    @classmethod
    def nice_name(cls, eptype: EndpointType) -> str:
        return {
            cls.GCP: "Globus Connect Personal",
            cls.GCSV5_ENDPOINT: "Globus Connect Server v5 Endpoint",
            cls.GUEST_COLLECTION: "Guest Collection",
            cls.MAPPED_COLLECTION: "Mapped Collection",
            cls.SHARE: "Shared Endpoint",
            cls.NON_GCSV5_ENDPOINT: "GCSv4 Endpoint",
        }.get(eptype, "UNKNOWN")

    @classmethod
    def determine_endpoint_type(cls, ep_doc: dict) -> EndpointType:
        """
        Given an endpoint document from transfer, determine what type of
        endpoint or collection it is for
        """
        if ep_doc.get("is_globus_connect") is True:
            return EndpointType.GCP

        if ep_doc.get("non_functional") is True:
            return EndpointType.GCSV5_ENDPOINT

        shared = ep_doc.get("host_endpoint_id") is not None

        if ep_doc.get("gcs_version"):
            try:
                major, _minor, _patch = ep_doc["gcs_version"].split(".")
            except ValueError:  # split -> unpack didn't give 3 values
                major = None

            gcsv5 = major == "5"
        else:
            gcsv5 = False

        if gcsv5:
            if shared:
                return EndpointType.GUEST_COLLECTION
            else:
                return EndpointType.MAPPED_COLLECTION

        elif shared:
            return EndpointType.SHARE

        return EndpointType.NON_GCSV5_ENDPOINT
