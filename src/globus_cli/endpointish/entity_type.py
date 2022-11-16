from __future__ import annotations

from enum import Enum


class EntityType(Enum):
    # endpoint / collection types, strings match entity_type value in
    # transfer endpoint docs
    GCP_MAPPED = "GCP_mapped_collection"
    GCP_GUEST = "GCP_guest_collection"
    GCSV5_ENDPOINT = "GCSv5_endpoint"
    GCSV5_MAPPED = "GCSv5_mapped_collection"
    GCSV5_GUEST = "GCSv5_guest_collection"
    GCSV4_HOST = "GCSv4_host"  # most likely GCSv4, but not necessarily
    GCSV4_SHARE = "GCSv4_share"
    UNRECOGNIZED = "UNRECOGNIZED"

    @classmethod
    def gcsv5_collections(cls) -> tuple[EntityType, ...]:
        return (cls.GCSV5_GUEST, cls.GCSV5_MAPPED)

    @classmethod
    def traditional_endpoints(cls) -> tuple[EntityType, ...]:
        return (cls.GCP_MAPPED, cls.GCP_GUEST, cls.GCSV4_HOST, cls.GCSV4_SHARE)

    @classmethod
    def non_gcsv5_collection_types(cls) -> tuple[EntityType, ...]:
        return tuple(x for x in cls if x not in cls.gcsv5_collections())

    @classmethod
    def gcsv5_types(cls) -> tuple[EntityType, ...]:
        return tuple(
            x for x in cls if (x is cls.GCSV5_ENDPOINT or x in cls.gcsv5_collections())
        )

    @classmethod
    def nice_name(cls, entitytype: EntityType) -> str:
        return {
            cls.GCP_MAPPED: "Globus Connect Personal Mapped Collection",
            cls.GCP_GUEST: "Globus Connect Personal Guest Collection",
            cls.GCSV5_ENDPOINT: "Globus Connect Server v5 Endpoint",
            cls.GCSV5_MAPPED: "Globus Connect Server v5 Mapped Collection",
            cls.GCSV5_GUEST: "Globus Connect Server v5 Guest Collection",
            cls.GCSV4_HOST: "Globus Connect Server v4 Host Endpoint",
            cls.GCSV4_SHARE: "Globus Connect Server v4 Shared Endpoint",
        }.get(entitytype, "UNRECOGNIZED")

    @classmethod
    def determine_entity_type(cls, ep_doc: dict) -> EntityType:
        try:
            return cls(ep_doc.get("entity_type"))
        except ValueError:
            return cls.UNRECOGNIZED
