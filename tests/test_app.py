import pathlib
import tempfile
import sys

# make src importable
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from typer.testing import CliRunner
from calctl.app import app

runner = CliRunner()

def test_cli_help():
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "calctl - A command-line calendar manager" in result.stdout
    assert "Commands:" in result.stdout

def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "calctl version 1.0.0" in result.stdout

def test_cli_add_event():
    with tempfile.TemporaryDirectory() as d:
        db = str(pathlib.Path(d) / "events.json")
        
        result = runner.invoke(app, [
            "--db", db, "add", 
            "--title", "CLI Test", 
            "--date", "2025-01-01", 
            "--time", "09:00",
            "--duration", "60"
        ])
        assert result.exit_code == 0
        assert "Added event" in result.stdout
        assert "CLI Test" in result.stdout

def test_cli_list():
    with tempfile.TemporaryDirectory() as d:
        db = str(pathlib.Path(d) / "events.json")
        
        # Add an event first
        runner.invoke(app, [
            "--db", db, "add",
            "--title", "List Test",
            "--date", "2025-01-01",
            "--time", "10:00", 
            "--duration", "30"
        ])
        
        # List events with explicit date range
        result = runner.invoke(app, ["--db", db, "list", "--from", "2025-01-01", "--to", "2025-12-31"])
        assert result.exit_code == 0
        assert "List Test" in result.stdout

def test_cli_show():
    with tempfile.TemporaryDirectory() as d:
        db = str(pathlib.Path(d) / "events.json")
        
        # Add event
        add_result = runner.invoke(app, [
            "--db", db, "add",
            "--title", "Show Test", 
            "--date", "2025-01-01",
            "--time", "11:00",
            "--duration", "45"
        ])
        assert add_result.exit_code == 0
        
        # Extract event ID from add output
        import re
        match = re.search(r'Added event (evt-\w+)', add_result.stdout)
        assert match
        event_id = match.group(1)
        
        # Show the event
        result = runner.invoke(app, ["--db", db, "show", event_id])
        assert result.exit_code == 0
        assert "Show Test" in result.stdout
        assert "Duration: 45 minutes" in result.stdout

def test_cli_edit():
    with tempfile.TemporaryDirectory() as d:
        db = str(pathlib.Path(d) / "events.json")
        
        # Add event
        add_result = runner.invoke(app, [
            "--db", db, "add",
            "--title", "Edit Me",
            "--date", "2025-01-01", 
            "--time", "12:00",
            "--duration", "60"
        ])
        assert add_result.exit_code == 0
        
        # Extract event ID
        import re
        match = re.search(r'Added event (evt-\w+)', add_result.stdout)
        assert match
        event_id = match.group(1)
        
        # Edit the event
        result = runner.invoke(app, [
            "--db", db, "edit", event_id,
            "--title", "Edited Title",
            "--duration", "90"
        ])
        assert result.exit_code == 0
        assert "Updated event" in result.stdout

def test_cli_delete_with_force():
    with tempfile.TemporaryDirectory() as d:
        db = str(pathlib.Path(d) / "events.json")
        
        # Add event
        add_result = runner.invoke(app, [
            "--db", db, "add",
            "--title", "Delete Me",
            "--date", "2025-01-01",
            "--time", "13:00", 
            "--duration", "30"
        ])
        assert add_result.exit_code == 0
        
        # Extract event ID
        import re
        match = re.search(r'Added event (evt-\w+)', add_result.stdout)
        assert match
        event_id = match.group(1)
        
        # Delete with force (skip confirmation)
        result = runner.invoke(app, [
            "--db", db, "delete", event_id, "--force"
        ])
        assert result.exit_code == 0
        assert "Deleted event" in result.stdout

def test_cli_search():
    with tempfile.TemporaryDirectory() as d:
        db = str(pathlib.Path(d) / "events.json")
        
        # Add searchable events
        runner.invoke(app, [
            "--db", db, "add",
            "--title", "Important Meeting",
            "--date", "2025-01-01",
            "--time", "14:00",
            "--duration", "60"
        ])
        
        runner.invoke(app, [
            "--db", db, "add", 
            "--title", "Casual Chat",
            "--date", "2025-01-01",
            "--time", "15:00",
            "--duration", "30"
        ])
        
        # Search for "meeting"
        result = runner.invoke(app, ["--db", db, "search", "meeting"])
        assert result.exit_code == 0
        assert "Important Meeting" in result.stdout
        assert "Casual Chat" not in result.stdout

def test_cli_agenda():
    with tempfile.TemporaryDirectory() as d:
        db = str(pathlib.Path(d) / "events.json")
        
        # Add events for agenda
        runner.invoke(app, [
            "--db", db, "add",
            "--title", "Morning Standup",
            "--date", "2025-01-01", 
            "--time", "09:00",
            "--duration", "30"
        ])
        
        runner.invoke(app, [
            "--db", db, "add",
            "--title", "Lunch Break",
            "--date", "2025-01-01",
            "--time", "12:00", 
            "--duration", "60"
        ])
        
        # Get agenda for specific date
        result = runner.invoke(app, ["--db", db, "agenda", "--date", "2025-01-01"])
        assert result.exit_code == 0
        # Check that both events are there
        assert "Morning Standup" in result.stdout
        assert "Lunch Break" in result.stdout
        assert "Total events: 2" in result.stdout

def test_cli_conflict_detection():
    with tempfile.TemporaryDirectory() as d:
        db = str(pathlib.Path(d) / "events.json")
        
        # Add first event
        result = runner.invoke(app, [
            "--db", db, "add",
            "--title", "First Event",
            "--date", "2025-01-01",
            "--time", "10:00",
            "--duration", "60"
        ])
        assert result.exit_code == 0
        
        # Try to add overlapping event (should fail)
        result = runner.invoke(app, [
            "--db", db, "add", 
            "--title", "Conflicting Event",
            "--date", "2025-01-01",
            "--time", "10:30",
            "--duration", "60"
        ])
        assert result.exit_code == 1
        assert "conflicts" in result.stdout.lower()

def test_cli_json_output():
    with tempfile.TemporaryDirectory() as d:
        db = str(pathlib.Path(d) / "events.json")
        
        # Add event
        runner.invoke(app, [
            "--db", db, "add",
            "--title", "JSON Test",
            "--date", "2025-01-01",
            "--time", "16:00",
            "--duration", "45"
        ])
        
        # List with JSON output - FIXED: Global flags come BEFORE command
        result = runner.invoke(app, ["--db", db, "--json", "list", "--from", "2025-01-01", "--to", "2025-12-31"])
        assert result.exit_code == 0
        
        # Should be valid JSON
        import json
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 1  # Only one event added
        assert data[0]["title"] == "JSON Test"