from globus_cli.principal_resolver import PrincipalResolver
from globus_cli.termio import Field, field_formatters

FLOW_SUMMARY_FORMAT_FIELDS = [
    Field("Flow ID", "id"),
    Field("Title", "title"),
    Field("Owner", PrincipalResolver("flow_owner").field),
    Field("Created At", "created_at", formatter=field_formatters.Date),
    Field("Updated At", "updated_at", formatter=field_formatters.Date),
]
