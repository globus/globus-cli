from globus_cli.commands._common import isoformat_to_local
from globus_cli.principal_resolver import PrincipalResolver

FLOW_SUMMARY_FORMAT_FIELDS = [
    ("Flow ID", "id"),
    ("Title", "title"),
    ("Owner", PrincipalResolver("flow_owner").field),
    ("Created At", lambda data: isoformat_to_local(data["created_at"])),
    ("Updated At", lambda data: isoformat_to_local(data["updated_at"])),
]
