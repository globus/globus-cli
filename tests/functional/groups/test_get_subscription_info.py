import uuid

from globus_sdk.testing import RegisteredResponse


def test_group_get_subscription_info_text(run_line):
    subscription_id = str(uuid.uuid1())
    group_id = str(uuid.uuid1())
    connector_id = str(uuid.uuid1())

    RegisteredResponse(
        service="groups",
        path=f"/subscription_info/{subscription_id}",
        json={
            "group_id": group_id,
            "subscription_id": subscription_id,
            "subscription_info": {
                "connectors": {
                    connector_id: {
                        "is_baa": False,
                        "is_ha": True,
                    }
                },
                "is_baa": False,
                "is_high_assurance": False,
            },
        },
    ).add()

    run_line(
        f"globus group get-subscription-info {subscription_id}",
        search_stdout=[
            ("Group ID", group_id),
            ("Subscription ID", subscription_id),
            ("BAA", "False"),
            ("High Assurance", "False"),
        ],
    )
