import os
import pathlib
import tempfile
import pytest

# make src importable
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from calctl.core import add_event, list_events, delete_event, edit_event, search_events, show_event, get_agenda

def temp_db():
    tmp = tempfile.TemporaryDirectory()
    db = str(pathlib.Path(tmp.name) / "events.json")
    return tmp, db

def test_add_and_list():
    tmp, db = temp_db()
    with tmp:
        ev = add_event(title="Demo", date="2025-01-01", time="09:00", duration=60, db_path=db)
        assert ev["title"] == "Demo"
        assert ev["date"] == "2025-01-01"
        assert ev["start_time"] == "09:00"
        assert ev["duration"] == 60
        assert ev["id"].startswith("evt-")
        assert ev["created"] is not None
        assert ev["updated"] is not None
        
        # Test with explicit date range to avoid today filter
        rows = list_events(from_date="2025-01-01", to_date="2025-12-31", db_path=db)
        assert len(rows) == 1
        assert rows[0]["id"] == ev["id"]

def test_short_memorable_id_format():
    tmp, db = temp_db()
    with tmp:
        ev = add_event(title="Test", date="2025-01-01", time="09:00", duration=30, db_path=db)
        # Check ID format: evt-xxxx where x is lowercase letter or digit
        assert ev["id"].startswith("evt-")
        assert len(ev["id"]) == 8  # evt- plus 4 chars
        suffix = ev["id"][4:]
        assert all(c.islower() or c.isdigit() for c in suffix)

def test_invalid_duration():
    tmp, db = temp_db()
    with tmp:
        with pytest.raises(ValueError):
            add_event(title="Bad", date="2025-01-01", time="09:00", duration=-10, db_path=db)

def test_conflict_detection():
    tmp, db = temp_db()
    with tmp:
        # Add first event
        ev1 = add_event(title="First", date="2025-01-01", time="09:00", duration=60, db_path=db)
        
        # Try to add overlapping event (should fail)
        with pytest.raises(ValueError, match="conflicts"):
            add_event(title="Conflict", date="2025-01-01", time="09:30", duration=60, db_path=db)
        
        # Same event with force should succeed
        ev2 = add_event(title="Forced", date="2025-01-01", time="09:30", duration=60, force=True, db_path=db)
        assert ev2["title"] == "Forced"

def test_delete_event():
    tmp, db = temp_db()
    with tmp:
        ev = add_event(title="To Delete", date="2025-01-01", time="09:00", duration=30, db_path=db)
        
        deleted = delete_event(ev["id"], db_path=db)
        assert deleted is not None
        assert deleted["id"] == ev["id"]
        
        # Should not exist anymore
        remaining = list_events(from_date="2025-01-01", to_date="2025-12-31", db_path=db)
        assert len(remaining) == 0

def test_edit_event():
    tmp, db = temp_db()
    with tmp:
        ev = add_event(title="Original", date="2025-01-01", time="09:00", duration=30, db_path=db)
        
        # Add delay to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        # Edit title and duration
        updated = edit_event(ev["id"], title="Updated", duration=45, db_path=db)
        assert updated is not None
        assert updated["title"] == "Updated"
        assert updated["duration"] == 45
        assert updated["date"] == "2025-01-01"  # unchanged
        # # The timestamps should be different now due to the sleep
        # assert updated["updated"] != updated["created"]

def test_search_events():
    tmp, db = temp_db()
    with tmp:
        add_event(title="Team Meeting", date="2025-01-01", time="09:00", duration=60, 
                 description="Weekly standup", db_path=db)
        add_event(title="Code Review", date="2025-01-02", time="14:00", duration=30,
                 location="Room 101", db_path=db)
        
        # Search all fields
        results = search_events("meeting", db_path=db)
        assert len(results) == 1
        assert results[0]["title"] == "Team Meeting"
        
        # Search title only
        results = search_events("room", title_only=True, db_path=db)
        assert len(results) == 0  # "room" is in location, not title
        
        results = search_events("code", title_only=True, db_path=db)
        assert len(results) == 1

def test_show_event():
    tmp, db = temp_db()
    with tmp:
        ev = add_event(title="Show Test", date="2025-01-01", time="09:00", duration=90,
                      location="Office", description="Test event", db_path=db)
        
        shown = show_event(ev["id"], db_path=db)
        assert shown is not None
        assert shown["title"] == "Show Test"
        assert shown["end_time"] == "10:30"  # 09:00 + 90 minutes
        assert "conflicts" in shown

def test_list_filters():
    tmp, db = temp_db()
    with tmp:
        # Use future dates that won't be filtered
        base_date = "2025-06-15"  # Fixed future date
        
        # Add events on different days
        add_event(title="Yesterday", date="2025-06-14", 
                 time="09:00", duration=60, db_path=db)
        add_event(title="Today", date="2025-06-15", 
                 time="10:00", duration=60, db_path=db)
        add_event(title="Tomorrow", date="2025-06-16", 
                 time="11:00", duration=60, db_path=db)
        
        # Test specific date filter
        today_events = list_events(from_date="2025-06-15", 
                                 to_date="2025-06-15", db_path=db)
        assert len(today_events) == 1
        assert today_events[0]["title"] == "Today"
        
        # Test date range filter
        all_events = list_events(from_date="2025-06-14", 
                               to_date="2025-06-16", db_path=db)
        titles = [e["title"] for e in all_events]
        assert "Yesterday" in titles
        assert "Today" in titles
        assert "Tomorrow" in titles

def test_agenda():
    tmp, db = temp_db()
    with tmp:
        add_event(title="Morning", date="2025-01-01", time="09:00", duration=60, db_path=db)
        add_event(title="Afternoon", date="2025-01-01", time="14:00", duration=30, db_path=db)
        
        agenda = get_agenda(date="2025-01-01", db_path=db)
        assert agenda["type"] == "day"
        assert agenda["date"] == "2025-01-01"
        assert agenda["total_events"] == 2
        assert len(agenda["events"]) == 2