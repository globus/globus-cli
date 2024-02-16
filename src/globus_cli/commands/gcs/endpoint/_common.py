from globus_cli.termio import Field, formatters

# https://docs.globus.org/globus-connect-server/v5.4/api/schemas/Endpoint_1_2_0_schema/
GCS_ENDPOINT_FIELDS = [
    Field("Endpoint ID", "id"),
    Field("Display Name", "display_name"),
    Field("Allow UDT", "allow_udt", formatter=formatters.FuzzyBool),
    Field("Contact Email", "contact_email"),
    Field("Contact Info", "contact_info"),
    Field("Department", "department"),
    Field("Description", "description"),
    Field("Earliest Last Access", "earliest_last_access", formatter=formatters.Date),
    Field("GCS Manager URL", "gcs_manager_url"),
    Field("GridFTP Control Channel Port", "gridftp_control_channel_port"),
    Field("Info Link", "info_link"),
    Field("Keywords", "keywords", formatter=formatters.Array),
    Field("Max Concurrency", "max_concurrency"),
    Field("Max Parallelism", "max_parallelism"),
    Field("Network Use", "network_use"),
    Field("Organization", "organization"),
    Field("Preferred Concurrency", "preferred_concurrency"),
    Field("Preferred Parallelism", "preferred_parallelism"),
    Field("Public", "public", formatter=formatters.FuzzyBool),
    Field("Subscription ID", "subscription_id"),
]
