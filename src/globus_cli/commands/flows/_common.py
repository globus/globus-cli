from globus_cli.principal_resolver import PrincipalResolver
from globus_cli.termio import Field

FLOW_SUMMARY_FORMAT_FIELDS = [
    ("Flow ID", "id"),
    ("Title", "title"),
    ("Owner", PrincipalResolver("flow_owner").field),
    Field("Created At", "created_at", formatter=Field.FormatName.Date),
    Field("Updated At", "updated_at", formatter=Field.FormatName.Date),
]
