from __future__ import annotations

import logging
import typing as t
import uuid

import globus_sdk
from globus_sdk.transport import (
    RetryCheckFlags,
    RetryCheckResult,
    RetryContext,
    set_retry_check_flags,
)

from globus_cli.login_manager import get_client_login, is_client_login

from .recursive_ls import RecursiveLsResponse

log = logging.getLogger(__name__)


@set_retry_check_flags(RetryCheckFlags.RUN_ONCE)
def _retry_client_consent(ctx: RetryContext) -> RetryCheckResult:
    """
    if using a client login automatically get needed consents by requesting
    the needed scopes
    """
    if (not is_client_login()) or (ctx.response is None):
        return RetryCheckResult.no_decision

    if ctx.response.status_code == 403:
        error_code = ctx.response.json().get("code")
        required_scopes = ctx.response.json().get("required_scopes")

        if error_code == "ConsentRequired" and required_scopes:
            client = get_client_login()
            client.oauth2_client_credentials_tokens(requested_scopes=required_scopes)
            return RetryCheckResult.do_retry

    return RetryCheckResult.no_decision


class CustomTransferClient(globus_sdk.TransferClient):
    def __init__(
        self,
        *,
        authorizer: globus_sdk.authorizers.GlobusAuthorizer,
        app_name: str,
    ) -> None:
        super().__init__(authorizer=authorizer, app_name=app_name)
        self.retry_config.checks.register_check(_retry_client_consent)

    # TODO: Remove this function when endpoints natively support recursive ls
    def recursive_operation_ls(
        self,
        endpoint_id: str | uuid.UUID,
        params: dict[str, t.Any],
        depth: int = 3,
    ) -> RecursiveLsResponse:
        """
        Makes recursive calls to ``GET /operation/endpoint/<endpoint_id>/ls``
        Does not preserve access to top level operation_ls fields, but
        adds a "path" field for every item that represents the full
        path to that item.

        :rtype: iterable of :class:`GlobusResponse <globus_sdk.response.GlobusResponse>`

        :param endpoint_id: The endpoint being recursively ls'ed. If no "path" is given
            in params, the start path is determined by this endpoint.
        :param params: Parameters that will be passed through as query params.
        :param depth: The maximum file depth the recursive ls will go to.
        """
        endpoint_id = str(endpoint_id)
        log.info(
            "TransferClient.recursive_operation_ls(%s, %s, %s)",
            endpoint_id,
            depth,
            params,
        )
        return RecursiveLsResponse(self, endpoint_id, params, max_depth=depth)
