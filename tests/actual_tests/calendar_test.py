import datetime

import pytest


@pytest.mark.asyncio(scope="session")
@pytest.mark.skip(reason="CalDAV not yet available in async-only mode")
async def test_create_delete_async(anc):
    principal = anc.cal.principal()

    calendar = principal.make_calendar("test_ncpyapi_basic")
    try:
        calendars = principal.calendars()
        assert calendars
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
    finally:
        calendar.delete()


@pytest.mark.asyncio(scope="session")
@pytest.mark.skip(reason="CalDAV not yet available in async-only mode")
async def test_multiple_calendars_async(anc):
    """Test creating, listing, and deleting multiple calendars (MKCALENDAR + PROPFIND + DELETE)."""
    principal = anc.cal.principal()
    calendars_before = principal.calendars()
    cal1 = principal.make_calendar("test_ncpyapi_multi_1")
    cal2 = principal.make_calendar("test_ncpyapi_multi_2")
    try:
        calendars_after = principal.calendars()
        new_names = {c.get_display_name() for c in calendars_after} - {c.get_display_name() for c in calendars_before}
        assert "test_ncpyapi_multi_1" in new_names
        assert "test_ncpyapi_multi_2" in new_names
    finally:
        cal1.delete()
        cal2.delete()
    assert len(principal.calendars()) == len(calendars_before)


@pytest.mark.asyncio(scope="session")
@pytest.mark.skip(reason="CalDAV not yet available in async-only mode")
async def test_calendar_rename_async(anc):
    """Test reading and updating calendar display name (PROPFIND + PROPPATCH)."""
    from caldav.elements.dav import DisplayName

    principal = anc.cal.principal()
    calendar = principal.make_calendar("test_ncpyapi_props")
    try:
        assert calendar.get_display_name() == "test_ncpyapi_props"
        calendar.set_properties([DisplayName("test_ncpyapi_renamed")])
        # Re-fetch to confirm server-side change
        refreshed = [c for c in principal.calendars() if c.get_display_name() == "test_ncpyapi_renamed"]
        assert len(refreshed) == 1
    finally:
        calendar.delete()


@pytest.mark.asyncio(scope="session")
@pytest.mark.skip(reason="CalDAV not yet available in async-only mode")
async def test_event_full_lifecycle_async(anc):
    """Test event create, read, update, delete — exercises PUT, PROPFIND, REPORT."""
    principal = anc.cal.principal()
    calendar = principal.make_calendar("test_ncpyapi_ops")
    try:
        # --- Event lifecycle ---
        now = datetime.datetime.now()
        calendar.save_event(
            dtstart=now,
            dtend=now + datetime.timedelta(hours=2),
            summary="Original Title",
        )
        assert len(calendar.events()) == 1

        fetched = calendar.events()[0]
        assert str(fetched.icalendar_component.get("SUMMARY")) == "Original Title"

        # Update event
        component = fetched.icalendar_component
        component["SUMMARY"] = "Updated Title"
        fetched.icalendar_instance.subcomponents[0] = component
        fetched.save()

        updated = calendar.events()[0]
        assert str(updated.icalendar_component.get("SUMMARY")) == "Updated Title"
        updated.delete()
        assert len(calendar.events()) == 0

        # --- Special characters in event (body encoding) ---
        calendar.save_event(
            dtstart=now,
            dtend=now + datetime.timedelta(hours=1),
            summary="Event with spëcial chars: <>&\"'",
        )
        fetched = calendar.events()[0]
        assert "spëcial chars" in str(fetched.icalendar_component.get("SUMMARY"))
        fetched.delete()
        assert len(calendar.events()) == 0
    finally:
        calendar.delete()


@pytest.mark.asyncio(scope="session")
@pytest.mark.skip(reason="CalDAV not yet available in async-only mode")
async def test_event_date_range_search_async(anc):
    """Test searching events by date range — exercises REPORT with XML body."""
    principal = anc.cal.principal()
    calendar = principal.make_calendar("test_ncpyapi_search")
    try:
        base = datetime.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
        calendar.save_event(
            dtstart=base,
            dtend=base + datetime.timedelta(hours=1),
            summary="Today Event",
        )
        calendar.save_event(
            dtstart=base + datetime.timedelta(days=1),
            dtend=base + datetime.timedelta(days=1, hours=1),
            summary="Tomorrow Event",
        )
        calendar.save_event(
            dtstart=base + datetime.timedelta(days=7),
            dtend=base + datetime.timedelta(days=7, hours=1),
            summary="Next Week Event",
        )
        assert len(calendar.events()) == 3

        # Search for today only
        results = calendar.search(
            start=base - datetime.timedelta(hours=1),
            end=base + datetime.timedelta(hours=2),
            event=True,
        )
        summaries = {str(e.icalendar_component.get("SUMMARY")) for e in results}
        assert "Today Event" in summaries
        assert "Tomorrow Event" not in summaries

        # Search for today + tomorrow
        results = calendar.search(
            start=base - datetime.timedelta(hours=1),
            end=base + datetime.timedelta(days=1, hours=2),
            event=True,
        )
        summaries = {str(e.icalendar_component.get("SUMMARY")) for e in results}
        assert "Today Event" in summaries
        assert "Tomorrow Event" in summaries
        assert "Next Week Event" not in summaries
    finally:
        calendar.delete()


@pytest.mark.asyncio(scope="session")
@pytest.mark.skip(reason="CalDAV not yet available in async-only mode")
async def test_todo_crud_async(anc):
    """Test todo create, read, complete, delete — exercises PUT + REPORT for VTODO."""
    principal = anc.cal.principal()
    calendar = principal.make_calendar("test_ncpyapi_todos")
    try:
        # Create
        todo = calendar.save_todo(
            summary="Test Todo Item",
            due=datetime.datetime.now() + datetime.timedelta(days=1),
        )
        todos = calendar.todos(include_completed=True)
        assert any(str(t.icalendar_component.get("SUMMARY")) == "Test Todo Item" for t in todos)

        # Update summary
        component = todo.icalendar_component
        component["SUMMARY"] = "Updated Todo Item"
        todo.icalendar_instance.subcomponents[0] = component
        todo.save()

        todos = calendar.todos(include_completed=True)
        assert any(str(t.icalendar_component.get("SUMMARY")) == "Updated Todo Item" for t in todos)

        # Complete
        todo.complete()
        open_todos = calendar.todos(include_completed=False)
        assert not any(str(t.icalendar_component.get("SUMMARY")) == "Updated Todo Item" for t in open_todos)
        completed_todos = calendar.todos(include_completed=True)
        assert any(str(t.icalendar_component.get("SUMMARY")) == "Updated Todo Item" for t in completed_todos)

        # Delete
        todo.delete()
        assert len(calendar.todos(include_completed=True)) == 0
    finally:
        calendar.delete()


@pytest.mark.asyncio(scope="session")
@pytest.mark.skip(reason="CalDAV not yet available in async-only mode")
async def test_caldav_available_property_async(anc):
    """Test that cal.available returns True when caldav is installed."""
    assert anc.cal.available is True


@pytest.mark.asyncio(scope="session")
@pytest.mark.skip(reason="CalDAV not yet available in async-only mode")
async def test_caldav_is_davclient_subclass_async(anc):
    """Test that _CalendarAPI is a proper DAVClient subclass."""
    from caldav.davclient import DAVClient

    assert isinstance(anc.cal, DAVClient)


@pytest.mark.asyncio(scope="session")
@pytest.mark.skip(reason="CalDAV not yet available in async-only mode")
async def test_caldav_huge_tree_attribute_async(anc):
    """Test that DAVClient attributes are accessible (validates super().__init__ compatibility)."""
    assert hasattr(anc.cal, "huge_tree")
    assert anc.cal.huge_tree is False


@pytest.mark.asyncio(scope="session")
@pytest.mark.skip(reason="CalDAV not yet available in async-only mode")
async def test_stub_when_caldav_unavailable_async():
    """Test the _CalendarAPI stub class behavior when caldav is not installed."""
    import importlib
    import sys

    # Temporarily hide caldav to trigger the ImportError branch
    caldav_modules = {name: mod for name, mod in sys.modules.items() if name == "caldav" or name.startswith("caldav.")}
    for name in caldav_modules:
        sys.modules[name] = None  # type: ignore

    try:
        # Force re-import of calendar_api to hit the ImportError branch
        if "nc_py_api.calendar_api" in sys.modules:
            del sys.modules["nc_py_api.calendar_api"]

        from nc_py_api.calendar_api import _CalendarAPI

        class _MockSession:
            class cfg:
                dav_endpoint = "http://localhost"

        stub = _CalendarAPI(_MockSession())
        assert stub.available is False
    finally:
        # Restore caldav modules
        for name, mod in caldav_modules.items():
            sys.modules[name] = mod
        # Re-import to restore the real class
        if "nc_py_api.calendar_api" in sys.modules:
            del sys.modules["nc_py_api.calendar_api"]
        importlib.import_module("nc_py_api.calendar_api")
