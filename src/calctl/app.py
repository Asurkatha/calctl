from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, List
import typer

from .core import (
    add_event, list_events, show_event, delete_event, 
    edit_event, search_events, get_agenda
)

app = typer.Typer(help="calctl - A command-line calendar manager")

@app.callback()
def main(
    db: Optional[str] = typer.Option(None, help="Path to events JSON database"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
    version: bool = typer.Option(False, "--version", help="Show version"),
):
    """calctl - A command-line calendar manager"""
    if version:
        typer.echo("calctl version 1.0.0")
        raise typer.Exit()

def echo_events(events: List[dict], json_out: bool = False):
    """Display events"""
    if json_out:
        typer.echo(json.dumps(events, indent=2))
        return
    
    if not events:
        typer.echo("No events.")
        return
    
    for event in events:
        typer.echo(f"{event['id']} | {event['title']} | {event['date']} | {event['start_time']}")

@app.command()
def add(
    title: str = typer.Option(..., help="Event title"),
    date: str = typer.Option(..., help="Date (YYYY-MM-DD)"),
    time: str = typer.Option(..., help="Start time (HH:MM)"),
    duration: int = typer.Option(..., help="Duration in minutes"),
    location: Optional[str] = typer.Option(None, help="Location"),
    description: Optional[str] = typer.Option(None, help="Description"),
    force: bool = typer.Option(False, "--force", help="Skip conflict validation"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    db: Optional[str] = typer.Option(None, help="Database path"),
):
    """Add a new event"""
    try:
        event = add_event(
            title=title, date=date, time=time, duration=duration,
            location=location, description=description, force=force,
            db_path=db
        )
        typer.echo(f"Added event {event['id']}")
        echo_events([event], json_out)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

@app.command("list")
def list_cmd(
    from_date: Optional[str] = typer.Option(None, "--from", help="From date"),
    to_date: Optional[str] = typer.Option(None, "--to", help="To date"),
    today: bool = typer.Option(False, "--today", help="Today's events"),
    week: bool = typer.Option(False, "--week", help="This week's events"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    db: Optional[str] = typer.Option(None, help="Database path"),
):
    """List events"""
    try:
        events = list_events(
            from_date=from_date, to_date=to_date, 
            today=today, week=week, db_path=db
        )
        echo_events(events, json_out)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def show(
    event_id: str = typer.Argument(help="Event ID"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    db: Optional[str] = typer.Option(None, help="Database path"),
):
    """Show event details"""
    try:
        event = show_event(event_id, db_path=db)
        if not event:
            typer.echo(f"Event {event_id} not found", err=True)
            raise typer.Exit(1)
        
        if json_out:
            typer.echo(json.dumps(event, indent=2))
        else:
            typer.echo(f"Event: {event['title']}")
            typer.echo(f"Date: {event['date']} {event['start_time']}")
            typer.echo(f"Duration: {event['duration']} minutes")
            if event.get('location'):
                typer.echo(f"Location: {event['location']}")
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
    db: Optional[str] = typer.Option(None, help="Database path"),
):
    """Edit an event"""
    try:
        updated = edit_event(
            event_id, title=title, date=date, time=time,
            duration=duration, location=location, description=description,
            db_path=db
        )
        if updated:
            typer.echo(f"Updated event {event_id}")
        else:
            typer.echo(f"Event {event_id} not found", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def delete(
    event_id: str = typer.Argument(help="Event ID"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
    db: Optional[str] = typer.Option(None, help="Database path"),
):
    """Delete an event"""
    try:
        if not force:
            event = show_event(event_id, db_path=db)
            if event:
                typer.echo(f"Delete '{event['title']}'?")
                if not typer.confirm("Continue?"):
                    typer.echo("Cancelled")
                    return
        
        deleted = delete_event(event_id, db_path=db)
        if deleted:
            typer.echo(f"Deleted event {event_id}")
        else:
            typer.echo(f"Event {event_id} not found", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def search(
    query: str = typer.Argument(help="Search query"),
    title_only: bool = typer.Option(False, "--title", help="Search titles only"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    db: Optional[str] = typer.Option(None, help="Database path"),
):
    """Search events"""
    try:
        results = search_events(query, title_only=title_only, db_path=db)
        echo_events(results, json_out)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def agenda(
    date: Optional[str] = typer.Option(None, "--date", help="Specific date"),
    week: bool = typer.Option(False, "--week", help="Week view"),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    db: Optional[str] = typer.Option(None, help="Database path"),
):
    """Show agenda"""
    try:
        agenda_data = get_agenda(date=date, week=week, db_path=db)
        
        if json_out:
            typer.echo(json.dumps(agenda_data, indent=2))
        else:
            typer.echo(f"Agenda for {agenda_data.get('date', 'week')}")
            typer.echo(f"Total events: {agenda_data['total_events']}")
            
            if agenda_data['type'] == 'day':
                for event in agenda_data['events']:
                    typer.echo(f"{event['start_time']} - {event['title']}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
