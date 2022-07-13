from __future__ import annotations

from .endpoint_type import EndpointType

SHOULD_USE_MAP = {
    "globus collection delete": [
        ("globus endpoint delete", EndpointType.traditional_endpoints()),
    ],
    "globus endpoint delete": [
        ("globus collection delete", EndpointType.collections()),
    ],
    "globus collection show": [
        ("globus endpoint show", EndpointType.non_collection_types()),
    ],
    "globus endpoint show": [
        ("globus collection show", EndpointType.collections()),
    ],
    "globus collection update": [
        ("globus endpoint update", EndpointType.traditional_endpoints()),
    ],
    "globus endpoint update": [
        ("globus collection update", EndpointType.collections()),
    ],
}


class WrongEndpointTypeError(ValueError):
    def __init__(
        self,
        from_command: str,
        endpoint_id: str,
        actual_type: EndpointType,
        expected_types: tuple[EndpointType, ...],
    ) -> None:
        self.from_command = from_command
        self.endpoint_id = str(endpoint_id)
        self.actual_type = actual_type
        self.expected_types = expected_types
        self.expected_message = self._get_expected_message()
        self.actual_message = self._get_actual_message()
        super().__init__(f"{self.expected_message} {self.actual_message}")

    def _get_expected_message(self) -> str:
        expect_str = ", ".join(EndpointType.nice_name(x) for x in self.expected_types)
        if len(self.expected_types) == 1:
            expect_str = f"a {expect_str}"
        else:
            expect_str = f"one of [{expect_str}]"
        return f"Expected {self.endpoint_id} to be {expect_str}."

    def _get_actual_message(self) -> str:
        actual_str = EndpointType.nice_name(self.actual_type)
        return f"Instead, found it was of type '{actual_str}'."

    def should_use_command(self) -> str | None:
        if self.from_command in SHOULD_USE_MAP:
            for should_use, if_types in SHOULD_USE_MAP[self.from_command]:
                if self.actual_type in if_types:
                    return should_use
        return None


class ExpectedCollectionError(WrongEndpointTypeError):
    def _get_expected_message(self) -> str:
        return f"Expected {self.endpoint_id} to be a collection ID."


class ExpectedEndpointError(WrongEndpointTypeError):
    def _get_expected_message(self) -> str:
        return f"Expected {self.endpoint_id} to be an endpoint ID."
