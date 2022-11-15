from __future__ import annotations

from enum import Enum


class EndpointType(Enum):
    # endpoint / collection types, strings match entity_type value in
    # transfer endpoint docs
    GCP_MAPPED = "GCP_mapped_collection"
    GCP_GUEST = "GCP_guest_collection"
    GCSV5_ENDPOINT = "GCSv5_endpoint"
    GCSV5_MAPPED = "GCSv5_mapped_collection"
    GCSV5_GUEST = "GCSv5_guest_collection"
    GCSv4_HOST = "GCSv4_host"  # most likely GCSv4, but not necessarily
    GCSv4_SHARE = "GCSv4_share"

    @classmethod
    def gcsv5_collections(cls) -> tuple[EndpointType, ...]:
        return (cls.GCSV5_GUEST, cls.GCSV5_MAPPED)

    @classmethod
    def traditional_endpoints(cls) -> tuple[EndpointType, ...]:
        return (cls.GCP_MAPPED, cls.GCP_GUEST, cls.GCSv4_HOST, cls.GCSv4_SHARE)

    @classmethod
    def non_gcsv5_collection_types(cls) -> tuple[EndpointType, ...]:
        return tuple(x for x in cls if x not in cls.gcsv5_collections())

    @classmethod
    def gcsv5_types(cls) -> tuple[EndpointType, ...]:
        return tuple(
            x for x in cls if (x is cls.GCSV5_ENDPOINT or x in cls.gcsv5_collections())
        )

    @classmethod
    def nice_name(cls, eptype: EndpointType) -> str:
        return {
            cls.GCP_MAPPED: "Globus Connect Personal Mapped Collection",
            cls.GCP_GUEST: "Globus Connect Personal Guest Collection",
            cls.GCSV5_ENDPOINT: "Globus Connect Server v5 Endpoint",
            cls.GCSV5_MAPPED: "Globus Connect Server v5 Mapped Collection",
            cls.GCSV5_GUEST: "Globus Connect Server v5 Guest Collection",
            cls.GCSv4_HOST: "Globus Connect Server v4 Host Endpoint",
            cls.GCSv4_SHARE: "Globus Connect Server v4 Shared Endpoint",
        }.get(eptype, "UNKNOWN")
