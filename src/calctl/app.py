from __future__ import annotations

import json
from typing import Optional, List
import typer

from .core import (
    add_event, list_events, show_event, delete_event,
    edit_event, search_events, get_agenda
)

app = typer.Typer(help="calctl - A command-line calendar manager")


# Global context for shared options
class Context:
    def __init__(self):
        self.db_path: Optional[str] = None
        self.json_output: bool = False
        self.plain: bool = False


# Global context instance
ctx = Context()


@app.callback(invoke_without_command=True)
def main(
    typer_ctx: typer.Context,
    db: Optional[str] = typer.Option(None,
                                     help="Path to events JSON database"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
    plain: bool = typer.Option(False, "--plain", help="Plain text output"),
    no_color: bool = typer.Option(False, "--no-color",
                                  help="Disable colored output"),
    version: bool = typer.Option(False, "--version", "-v",
                                 help="Show version"),
):
    """calctl - A command-line calendar manager"""
    # Set global context
    ctx.db_path = db
    ctx.json_output = json_out
    ctx.plain = plain

    if version:
        typer.echo("calctl version 1.0.0")
        raise typer.Exit(0)

    if typer_ctx.invoked_subcommand is None:
        typer.echo("calctl - A command-line calendar manager")
        typer.echo()
        typer.echo("Usage: calctl [options] <command> [arguments]")
        typer.echo()
        typer.echo("Commands:")
        typer.echo("  add       Add a new event")
        typer.echo("  list      List events")
        typer.echo("  show      Show event details")
        typer.echo("  edit      Edit an event")
        typer.echo("  delete    Delete event(s)")
        typer.echo("  search    Search events")
        typer.echo("  agenda    Show agenda view")
        typer.echo()
        typer.echo("Options:")
        typer.echo("  -h, --help     Show help")
        typer.echo("  -v, --version  Show version")
        typer.echo("  --json         Output in JSON format")
        typer.echo("  --plain        Plain text output")
        typer.echo()
        typer.echo("Examples:")
        msg = ('  calctl add --title "Meeting tomorrow at 2pm" '
               '--date 2025-01-15 --time 14:00 --duration 60')
        typer.echo(msg)
        typer.echo("  calctl list --today")
        typer.echo("  calctl agenda --week")
        raise typer.Exit(0)


def echo_events(events: List[dict]):
    """Display events using global context"""
    if ctx.json_output:
        typer.echo(json.dumps(events, indent=2))
        return

    if not events:
        typer.echo("No events.")
        return

    for event in events:
        parts = [event['id'], event['title'], event['date'],
                 event['start_time']]
        typer.echo(" | ".join(parts))


@app.command()
def add(
    title: str = typer.Option(..., help="Event title"),
    date: str = typer.Option(..., help="Date (YYYY-MM-DD)"),
    time: str = typer.Option(..., help="Start time (HH:MM)"),
    duration: int = typer.Option(..., help="Duration in minutes"),
    location: Optional[str] = typer.Option(None, help="Location"),
    description: Optional[str] = typer.Option(None, help="Description"),
    force: bool = typer.Option(False, "--force",
                               help="Skip conflict validation"),
):
    """Add a new event"""
    try:
        event = add_event(
            title=title, date=date, time=time, duration=duration,
            location=location, description=description, force=force,
            db_path=ctx.db_path
        )
        typer.echo(f"Added event {event['id']}")
        echo_events([event])
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("list")
def list_cmd(
    from_date: Optional[str] = typer.Option(None, "--from",
                                            help="From date"),
    to_date: Optional[str] = typer.Option(None, "--to", help="To date"),
    today: bool = typer.Option(False, "--today", help="Today's events"),
    week: bool = typer.Option(False, "--week", help="This week's events"),
):
    """List events"""
    try:
        events = list_events(
            from_date=from_date, to_date=to_date,
            today=today, week=week, db_path=ctx.db_path
        )
        echo_events(events)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def show(
    event_id: str = typer.Argument(help="Event ID"),
):
    """Show event details"""
    try:
        event = show_event(event_id, db_path=ctx.db_path)
        if not event:
            typer.echo(f"Event {event_id} not found", err=True)
            raise typer.Exit(1)

        if ctx.json_output:
            typer.echo(json.dumps(event, indent=2))
        else:
            typer.echo(f"Event: {event['title']}")
            typer.echo(f"ID: {event['id']}")
            typer.echo(f"Date: {event['date']} {event['start_time']}")
            typer.echo(f"Duration: {event['duration']} minutes")
            if event.get('location'):
                typer.echo(f"Location: {event['location']}")
            if event.get('description'):
                typer.echo(f"Description: {event['description']}")
            typer.echo(f"Created: {event['created']}")
            typer.echo(f"Updated: {event['updated']}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def edit(
    event_id: str = typer.Argument(help="Event ID"),
    title: Optional[str] = typer.Option(None, help="New title"),
    date: Optional[str] = typer.Option(None, help="New date"),
    time: Optional[str] = typer.Option(None, help="New time"),
    duration: Optional[int] = typer.Option(None, help="New duration"),
    location: Optional[str] = typer.Option(None, help="New location"),
    description: Optional[str] = typer.Option(None, help="New description"),
):
    """Edit an event"""
    try:
        updated = edit_event(
            event_id, title=title, date=date, time=time,
            duration=duration, location=location, description=description,
            db_path=ctx.db_path
        )
        if updated:
            typer.echo(f"Updated event {event_id}")
            echo_events([updated])
        else:
            typer.echo(f"Event {event_id} not found", err=True)
            raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def delete(
    event_id: str = typer.Argument(help="Event ID"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Delete an event"""
    try:
        # Get event info first
        event = show_event(event_id, db_path=ctx.db_path)
        if not event:
            typer.echo(f"Event {event_id} not found", err=True)
            raise typer.Exit(1)

        # Ask for confirmation unless force
        if not force:
            msg = (f"About to delete: {event['title']} on {event['date']} "
                   f"at {event['start_time']}")
            typer.echo(msg)
            if not typer.confirm("Are you sure?"):
                typer.echo("Cancelled")
                return

        # Delete the event
        deleted = delete_event(event_id, db_path=ctx.db_path)
        if deleted:
            typer.echo(f"Deleted event {event_id}")
        else:
            typer.echo(f"Failed to delete event {event_id}", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(help="Search query"),
    title: bool = typer.Option(False, "--title", help="Search titles only"),
):
    """Search events"""
    try:
        results = search_events(query, title_only=title, db_path=ctx.db_path)
        echo_events(results)
        if not ctx.json_output and results:
            typer.echo(f"\nFound {len(results)} matching events")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def agenda(
    date: Optional[str] = typer.Option(None, "--date", help="Specific date"),
    week: bool = typer.Option(False, "--week", help="Week view"),
):
    """Show agenda"""
    try:
        agenda_data = get_agenda(date=date, week=week, db_path=ctx.db_path)

        if ctx.json_output:
            typer.echo(json.dumps(agenda_data, indent=2))
        else:
            target = agenda_data.get('date', 'week')
            typer.echo(f"Agenda for {target}")
            typer.echo(f"Total events: {agenda_data['total_events']}")

            if agenda_data['type'] == 'day':
                for event in agenda_data['events']:
                    from .core import Event
                    event_obj = Event.from_dict(event)
                    typer.echo(f"{event['start_time']} - {event['title']}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()