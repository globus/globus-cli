from __future__ import annotations

import logging
import textwrap
import typing as t
import uuid

import click
import globus_sdk
from globus_sdk.transport import (
    RetryCheckFlags,
    RetryCheckResult,
    RetryContext,
    set_retry_check_flags,
)

from globus_cli.login_manager import get_client_login, is_client_login

from .data import display_name_or_cname
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
        self.transport.register_retry_check(_retry_client_consent)

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

    def get_endpoint_w_server_list(
        self, endpoint_id: str | uuid.UUID
    ) -> tuple[
        globus_sdk.GlobusHTTPResponse, str | globus_sdk.IterableTransferResponse
    ]:
        """
        A helper for handling endpoint server list lookups correctly accounting
        for various endpoint types.

        - Raises click.UsageError when used on Shares
        - Returns (<get_endpoint_response>, "S3") for S3 endpoints
        - Returns (<get_endpoint_response>, <server_list_response>) for all other
          Endpoints
        """
        endpoint = self.get_endpoint(endpoint_id)

        if endpoint["host_endpoint_id"]:  # not GCS -- this is a share endpoint
            raise click.UsageError(
                textwrap.dedent(
                    """\
                {id} ({0}) is a share and does not have servers.

                To see details of the share, use
                    globus endpoint show {id}

                To list the servers on the share's host endpoint, use
                    globus endpoint server list {host_endpoint_id}
            """
                ).format(display_name_or_cname(endpoint), **endpoint.data)
            )

        if endpoint["s3_url"]:  # not GCS -- legacy S3 endpoint type
            return (endpoint, "S3")

        else:
            return (endpoint, self.endpoint_server_list(endpoint_id))
