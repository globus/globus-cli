from __future__ import annotations

import logging
import typing as t
import uuid

import click
import globus_sdk

from .entity_type import EntityType
from .errors import ExpectedCollectionError, ExpectedEndpointError, WrongEntityTypeError

log = logging.getLogger(__name__)


class Endpointish:
    def __init__(
        self,
        endpoint_id: str | uuid.UUID,
        *,
        transfer_client: globus_sdk.TransferClient,
    ):
        self._client = transfer_client
        self.endpoint_id = endpoint_id

        log.debug("Endpointish getting ep data")
        res = self._client.get_endpoint(endpoint_id)
        self.data = res.data
        log.debug("Endpointish.data=%s", self.data)

        log.debug("Endpointish determine entity type")
        self.entity_type = EntityType.determine_entity_type(self.data)
        log.debug("Endpointish.entity_type=%s", self.entity_type)

    @property
    def nice_type_name(self) -> str:
        return EntityType.nice_name(self.entity_type)

    def assert_entity_type(
        self,
        expect_types: tuple[EntityType, ...] | EntityType,
        error_class: type[WrongEntityTypeError] = WrongEntityTypeError,
    ) -> None:
        if isinstance(expect_types, EntityType):
            expect_types = (expect_types,)
        if self.entity_type not in expect_types:
            raise error_class(
                click.get_current_context().command_path,
                str(self.endpoint_id),
                self.entity_type,
                expect_types,
            )

    def assert_is_gcsv5_collection(self) -> None:
        self.assert_entity_type(
            EntityType.gcsv5_collections(), error_class=ExpectedCollectionError
        )

    def assert_is_not_gcsv5_collection(self) -> None:
        self.assert_entity_type(
            EntityType.non_gcsv5_collection_types(), error_class=ExpectedEndpointError
        )

    def assert_is_traditional_endpoint(self) -> None:
        self.assert_entity_type(
            EntityType.traditional_endpoints(), error_class=ExpectedEndpointError
        )

    def get_collection_endpoint_id(self) -> str:
        self.assert_is_gcsv5_collection()
        return t.cast(str, self.data["owner_id"])

    def get_gcs_address(self) -> str:
        self.assert_entity_type(EntityType.gcsv5_types())
        return t.cast(str, self.data["DATA"][0]["hostname"])

    @property
    def requires_data_access_scope(self) -> bool:
        if self.entity_type is EntityType.GCSV5_MAPPED:
            if self.data.get("high_assurance") is False:
                return True
        return False

    @property
    def is_managed(self) -> bool:
        if self.data.get("subscription_id") is None:
            return False
        return True
