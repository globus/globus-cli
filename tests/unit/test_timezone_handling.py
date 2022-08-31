import datetime

from globus_cli.commands.timer.create.transfer import resolve_start_time

EST = datetime.timezone(datetime.timedelta(hours=-5), name="EST")


def test_resolve_start_time_defaults_to_now():
    value = resolve_start_time(None)
    assert isinstance(value, datetime.datetime)
    assert value.tzinfo is not None
    # check for closeness, rather than being exact
    assert (datetime.datetime.now().astimezone() - value) < datetime.timedelta(
        seconds=1
    )


def test_resolve_start_time_preserves_existing_tzinfo():
    original = datetime.datetime.now().astimezone(EST)
    resolved = resolve_start_time(original)
    assert resolved.tzinfo == EST
    assert resolved == original


def test_resolve_start_time_adds_tzinfo_if_missing():
    original = datetime.datetime.now()
    resolved = resolve_start_time(original)
    assert resolved.tzinfo is not None

    # but the true time represented remains the same if normalized to a given timezone
    # (UTC and EST both tested to guard against potential variations if a developer's
    # local time matches one of these and that impacts behavior unexpectedly)
    assert original.astimezone(datetime.timezone.utc) == resolved.astimezone(
        datetime.timezone.utc
    )
    assert original.astimezone(EST) == resolved.astimezone(EST)
