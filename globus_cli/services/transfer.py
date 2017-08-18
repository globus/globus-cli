import uuid
import random
import time
import click

try:
    import cryptography
    # slightly hacky way of preventing flake8 from complaining
    cryptography_imported = bool(cryptography)
except ImportError:
    cryptography_imported = False

from globus_sdk import TransferClient, RefreshTokenAuthorizer
from globus_sdk.exc import NetworkError
from globus_sdk.base import safe_stringify

from globus_cli import version
from globus_cli.safeio import safeprint
from globus_cli.config import (
    get_transfer_tokens, internal_auth_client, set_transfer_access_token)
from globus_cli.parsing import EXPLICIT_NULL
from globus_cli.services.recursive_ls import RecursiveLsResponse


class RetryingTransferClient(TransferClient):
    """
    Wrapper around TransferClient that retries safe resources on NetworkErrors
    """

    def __init__(self, tries=10, *args, **kwargs):
        super(RetryingTransferClient, self).__init__(*args, **kwargs)
        self.tries = tries

    def retry(self, f, *args, **kwargs):
        """
        Retries the given function self.tries times on NetworkErros
        """
        backoff = random.random() / 100  # 5ms on average
        for t in range(self.tries-1):
            try:
                return f(*args, **kwargs)
            except NetworkError:
                time.sleep(backoff)
                backoff *= 2
        return f(*args, **kwargs)

    # get and put should always be safe to retry
    def get(self, *args, **kwargs):
        return self.retry(
            super(RetryingTransferClient, self).get, *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.retry(
            super(RetryingTransferClient, self).put, *args, **kwargs)

    # task submission is safe, as the data contains a unique submission-id
    def submit_transfer(self, *args, **kwargs):
        return self.retry(super(
            RetryingTransferClient, self).submit_transfer, *args, **kwargs)

    def submit_delete(self, *args, **kwargs):
        return self.retry(super(
            RetryingTransferClient, self).submit_delete, *args, **kwargs)

    # TDOD: Remove this function when endpoints natively support recursive ls
    def recursive_operation_ls(self, endpoint_id,
                               depth=3, follow_symlinks=False,
                               filter_after_first=True, **params):
        """
        Makes recursive calls to ``GET /operation/endpoint/<endpoint_id>/ls``
        Does not preserve access to top level operation_ls fields, but
        adds a "path" field for every item that represents the full
        path to that item.
        :rtype: iterable of :class:`GlobusResponse
                <globus_sdk.response.GlobusResponse>`
        **Parameters**
            ``endpoint_id`` (*string*)
              The endpoint being recursively ls'ed. If no "path" is given in
              params, the start path is determined by this endpoint.
            ``depth`` (*int*)
              The maximum file depth the recursive ls will go to.
            ``filter_after_first`` (*bool*)
              If False, any "filter" in params will only be applied to the
              first, top level ls, all results beyond that will be unfiltered.
            ``params``
              Parameters that will be passed through as query params.
        **Examples**
        >>> tc = globus_sdk.TransferClient(...)
        >>> for entry in tc.recursive_operation_ls(ep_id, path="/~/project1/"):
        >>>     print(entry["path"], entry["type"])
        **External Documentation**
        See
        `List Directory Contents \
        <https://docs.globus.org/api/transfer/file_operations/#list_directory_contents>`_
        in the REST documentation for details, but note that top level data
        fields are no longer available and an additional per item
        "path" field is added.
        """
        endpoint_id = safe_stringify(endpoint_id)
        self.logger.info("TransferClient.recursive_operation_ls({}, {}, {})"
                         .format(endpoint_id, depth, params))
        return RecursiveLsResponse(self, endpoint_id, depth, follow_symlinks,
                                   filter_after_first, params)


def _update_access_tokens(token_response):
    tokens = token_response.by_resource_server['transfer.api.globus.org']
    set_transfer_access_token(tokens['access_token'],
                              tokens['expires_at_seconds'])


def get_client():
    tokens = get_transfer_tokens()
    authorizer = None

    # if there's a refresh token, use it to build the authorizer
    if tokens['refresh_token'] is not None:
        authorizer = RefreshTokenAuthorizer(
            tokens['refresh_token'], internal_auth_client(),
            tokens['access_token'], tokens['access_token_expires'],
            on_refresh=_update_access_tokens)

    return RetryingTransferClient(
        tries=10, authorizer=authorizer, app_name=version.app_name)


def display_name_or_cname(ep_doc):
    return ep_doc['display_name'] or ep_doc['canonical_name']


def iterable_response_to_dict(iterator):
    output_dict = {'DATA': []}
    for item in iterator:
        dat = item
        try:
            dat = item.data
        except AttributeError:
            pass
        output_dict['DATA'].append(dat)
    return output_dict


def assemble_generic_doc(datatype, **kwargs):
    doc = {'DATA_TYPE': datatype}
    for key, val in kwargs.items():
        if isinstance(val, uuid.UUID):
            val = str(val)

        if val == EXPLICIT_NULL:
            doc[key] = None
        elif val is not None:
            doc[key] = val
    return doc


def supported_activation_methods(res):
    """
    Given an activation_requirements document
    returns a list of activation methods supported by this endpoint.
    """
    supported = ["web"]  # web activation is always supported.

    # oauth
    if res["oauth_server"]:
        supported.append("oauth")

    for req in res["DATA"]:
        # myproxy
        if (req["type"] == "myproxy" and req["name"] == "hostname" and
                req["value"] != "myproxy.globusonline.org"):
            supported.append("myproxy")

        # delegate_proxy
        if req["type"] == "delegate_proxy" and req["name"] == "public_key":
            supported.append("delegate_proxy")

    return supported


def activation_requirements_help_text(res, ep_id):
    """
    Given an activation requirements document and an endpoint_id
    returns a string of help text for how to activate the endpoint
    """
    methods = supported_activation_methods(res)

    lines = [
        "This endpoint supports the following activation methods: ",
        ", ".join(methods).replace("_", " "),
        "\n",

        ("For web activation use:\n"
         "'globus endpoint activate --web {}'\n".format(ep_id)
         if "web" in methods else ""),

        ("For myproxy activation use:\n"
         "'globus endpoint activate --myproxy {}'\n".format(ep_id)
         if "myproxy" in methods else ""),

        ("For oauth activation use web activation:\n"
         "'globus endpoint activate --web {}'\n".format(ep_id)
         if "oauth" in methods else ""),

        ("For delegate proxy activation use:\n"
         "'globus endpoint activate --delegate-proxy "
         "X.509_PEM_FILE {}'\n".format(ep_id)
         if "delegate_proxy" in methods and cryptography_imported else ""),

        ("Delegate proxy activation requires an additional dependency on "
         "cryptography. See the docs for details:\n"
         "https://docs.globus.org/cli/reference/endpoint_activate/\n"
         if "delegate_proxy" in methods and not cryptography_imported else ""),
    ]

    return "".join(lines)


def autoactivate(client, endpoint_id, if_expires_in=None):
    """
    Attempts to auto-activate the given endpoint with the given client
    If auto-activation fails, parses the returned activation requirements
    to determine which methods of activation are supported, then tells
    the user to use 'globus endpoint activate' with the correct options(s)
    """
    kwargs = {}
    if if_expires_in is not None:
        kwargs['if_expires_in'] = if_expires_in

    res = client.endpoint_autoactivate(endpoint_id, **kwargs)
    if res["code"] == "AutoActivationFailed":

        message = ("The endpoint could not be auto-activated and must be "
                   "activated before it can be used.\n\n" +
                   activation_requirements_help_text(res, endpoint_id))

        safeprint(message, write_to_stderr=True)
        click.get_current_context().exit(1)

    else:
        return res


ENDPOINT_LIST_FIELDS = (('ID', 'id'), ('Owner', 'owner_string'),
                        ('Display Name', display_name_or_cname))
