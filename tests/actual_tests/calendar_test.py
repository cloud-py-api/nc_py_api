import datetime

import pytest


def test_create_delete(nc):
    if nc.cal.available is False:
        pytest.skip("caldav package is not installed")

    principal = nc.cal.principal()
    calendars = principal.calendars()
    assert calendars
    calendar = calendars[0]
    all_events_before = calendar.events()
    event = calendar.save_event(
        dtstart=datetime.datetime.now(),
        dtend=datetime.datetime.now() + datetime.timedelta(hours=1),
        summary="NcPyApi + CalDAV test",
    )
    all_events_after = calendar.events()
    assert len(all_events_after) == len(all_events_before) + 1
    event.delete()
    assert len(calendar.events()) == len(all_events_before)
