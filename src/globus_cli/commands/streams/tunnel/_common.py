from globus_cli.termio import Field

TUNNEL_STANDARD_FIELDS = [
    Field("ID", "id"),
    Field("Label", "attributes.label"),
    Field("State", "attributes.state"),
    Field("Status", "attributes.status"),
    Field("Listener Access Point", "relationships.listener.data.id"),
    Field("Listener IP", "attributes.listener.data.ip_address"),
    Field("Listener Port", "attributes.listener.data.port"),
    Field("Initiator Access Point", "relationships.initiator.data.id"),
    Field("Initiator IP", "attributes.initiator.data.ip_address"),
    Field("Initiator Port", "attributes.initiator.data.port"),
]
