import datetime

import globus_sdk

from globus_cli.commands.timer.create._common import _to_local_tz

EST = datetime.timezone(datetime.timedelta(hours=-5), name="EST")


def test_timer_create_local_tz_conversion_of_missing():
    value = _to_local_tz(None)
    assert value is globus_sdk.MISSING


def test_timer_create_local_tz_conversion_preserves_existing_tzinfo():
    original = datetime.datetime.now().astimezone(EST)
    resolved = _to_local_tz(original)
    assert resolved.tzinfo == EST
    assert resolved == original


def test_timer_create_local_tz_conversion_adds_tzinfo_if_missing():
    original = datetime.datetime.now()
    resolved = _to_local_tz(original)
    assert resolved.tzinfo is not None

    # but the true time represented remains the same if normalized to a given timezone
    # (UTC and EST both tested to guard against potential variations if a developer's
    # local time matches one of these and that impacts behavior unexpectedly)
    assert original.astimezone(datetime.timezone.utc) == resolved.astimezone(
        datetime.timezone.utc
    )
    assert original.astimezone(EST) == resolved.astimezone(EST)
