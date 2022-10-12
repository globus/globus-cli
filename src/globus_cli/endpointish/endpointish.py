from __future__ import annotations

import logging
import uuid
from typing import cast

import click
import globus_sdk

from .endpoint_type import EndpointType
from .errors import (
    ExpectedCollectionError,
    ExpectedEndpointError,
    WrongEndpointTypeError,
)

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

        log.debug("Endpointish determine ep type")
        self.ep_type = EndpointType.determine_endpoint_type(self.data)
        log.debug("Endpointish.ep_type=%s", self.ep_type)

    @property
    def nice_type_name(self) -> str:
        return EndpointType.nice_name(self.ep_type)

    def assert_ep_type(
        self,
        expect_types: tuple[EndpointType, ...] | EndpointType,
        error_class: type[WrongEndpointTypeError] = WrongEndpointTypeError,
    ) -> None:
        if isinstance(expect_types, EndpointType):
            expect_types = (expect_types,)
        if self.ep_type not in expect_types:
            raise error_class(
                click.get_current_context().command_path,
                str(self.endpoint_id),
                self.ep_type,
                expect_types,
            )

    def assert_is_gcsv5_collection(self) -> None:
        self.assert_ep_type(
            EndpointType.collections(), error_class=ExpectedCollectionError
        )

    def assert_is_not_collection(self) -> None:
        self.assert_ep_type(
            EndpointType.non_collection_types(), error_class=ExpectedEndpointError
        )

    def assert_is_traditional_endpoint(self) -> None:
        self.assert_ep_type(
            EndpointType.traditional_endpoints(), error_class=ExpectedEndpointError
        )

    def get_collection_endpoint_id(self) -> str:
        self.assert_is_gcsv5_collection()
        return cast(str, self.data["owner_id"])

    def get_gcs_address(self) -> str:
        self.assert_ep_type(EndpointType.gcsv5_types())
        return cast(str, self.data["DATA"][0]["hostname"])

    @property
    def requires_data_access_scope(self) -> bool:
        if self.ep_type is EndpointType.MAPPED_COLLECTION:
            if self.data.get("high_assurance") is False:
                return True
        return False
