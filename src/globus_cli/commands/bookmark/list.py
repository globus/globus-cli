import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, field_formatters, formatted_print


class EndpointIdToNameFormatter(field_formatters.StrFieldFormatter):
    def __init__(self, client: globus_sdk.TransferClient) -> None:
        self.client = client

    def render(self, value: str) -> str:
        from globus_cli.services.transfer import display_name_or_cname

        try:
            ep_doc = self.client.get_endpoint(value)
            return display_name_or_cname(ep_doc)
        except globus_sdk.TransferAPIError as err:
            if err.code == "EndpointDeleted":
                return "[DELETED ENDPOINT]"
            else:
                raise err


@command(
    "list",
    adoc_output="""When textual output is requested, the following fields are displayed:
- 'Name'
- 'Bookmark ID'
- 'Endpoint ID'
- 'Endpoint Name'
- 'Path'
""",
    adoc_examples="""
[source,bash]
----
$ globus bookmark list
----

Format specific fields in the bookmark list into unix-friendly columnar
output:

[source,bash]
----
$ globus bookmark list --jmespath='DATA[*].[name, endpoint_id]' --format=unix
----
""",
    short_help="List your bookmarks",
)
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def bookmark_list(*, login_manager: LoginManager):
    """List all bookmarks for the current user"""
    from globus_cli.services.transfer import iterable_response_to_dict

    transfer_client = login_manager.get_transfer_client()

    bookmark_iterator = transfer_client.bookmark_list()

    formatted_print(
        bookmark_iterator,
        fields=[
            Field("Name", "name"),
            Field("Bookmark ID", "id"),
            Field("Endpoint ID", "endpoint_id"),
            Field(
                "Endpoint Name",
                "endpoint_id",
                formatter=EndpointIdToNameFormatter(transfer_client),
            ),
            Field("Path", "path"),
        ],
        response_key="DATA",
        json_converter=iterable_response_to_dict,
    )
