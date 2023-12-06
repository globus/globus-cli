import datetime

import globus_sdk

from globus_cli.commands.timer.create.transfer import resolve_optional_local_time

EST = datetime.timezone(datetime.timedelta(hours=-5), name="EST")


def test_resolve_optional_local_time_converts_none_to_missing():
    value = resolve_optional_local_time(None)
    assert value is globus_sdk.MISSING


def test_resolve_optional_local_time_preserves_existing_tzinfo():
    original = datetime.datetime.now().astimezone(EST)
    resolved = resolve_optional_local_time(original)
    assert resolved.tzinfo == EST
    assert resolved == original


def test_resolve_optional_local_time_adds_tzinfo_if_missing():
    original = datetime.datetime.now()
    resolved = resolve_optional_local_time(original)
    assert resolved.tzinfo is not None

    # but the true time represented remains the same if normalized to a given timezone
    # (UTC and EST both tested to guard against potential variations if a developer's
    # local time matches one of these and that impacts behavior unexpectedly)
    assert original.astimezone(datetime.timezone.utc) == resolved.astimezone(
        datetime.timezone.utc
    )
    assert original.astimezone(EST) == resolved.astimezone(EST)
