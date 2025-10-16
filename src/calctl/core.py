from __future__ import annotations

import secrets
import string
import time as time_module
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from dateutil.parser import parse as parse_dt
from .storage import load_events, save_events

ISO = "%Y-%m-%dT%H:%M:%S"


def _to_iso(dt: datetime) -> str:
    return dt.strftime(ISO)


def _from_iso(s: str) -> datetime:
    return datetime.strptime(s, ISO)


def _generate_short_id() -> str:
    """Generate short memorable ID in format evt-7d3f"""
    chars = string.ascii_lowercase + string.digits
    suffix = "".join(secrets.choice(chars) for _ in range(4))
    return f"evt-{suffix}"


def _ensure_unique_id(events: List[Dict], proposed_id: str) -> str:
    """Ensure the proposed ID is unique, regenerate if needed"""
    existing_ids = {e.get("id") for e in events}
    while proposed_id in existing_ids:
        proposed_id = _generate_short_id()
    return proposed_id


@dataclass
class Event:
    id: str
    title: str
    date: str  # ISO date part (YYYY-MM-DD)
    start_time: str  # HH:MM format
    duration: int  # minutes
    location: Optional[str] = None
    description: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Event":
        return Event(**d)

    def get_start_datetime(self) -> datetime:
        """Get full start datetime"""
        date_part = datetime.fromisoformat(self.date).date()
        time_part = datetime.strptime(self.start_time, "%H:%M").time()
        return datetime.combine(date_part, time_part)

    def get_end_datetime(self) -> datetime:
        """Calculate end datetime from start + duration"""
        start_dt = self.get_start_datetime()
        return start_dt + timedelta(minutes=self.duration)


def _parse_date_time(date_str: str, time_str: str) -> Tuple[str, str]:
    """Parse and validate date and time strings"""
    if time_str:
        full_str = f"{date_str} {time_str}"
        parsed_dt = parse_dt(full_str)
    else:
        parsed_dt = parse_dt(date_str)

    date_part = parsed_dt.strftime("%Y-%m-%d")
    time_part = parsed_dt.strftime("%H:%M")

    return date_part, time_part


def _check_conflicts(
    events: List[Dict], new_event: Event, exclude_id: Optional[str] = None
) -> List[Dict]:
    """Check for scheduling conflicts with existing events"""
    conflicts = []
    new_start = new_event.get_start_datetime()
    new_end = new_event.get_end_datetime()

    for event in events:
        if exclude_id and event.get("id") == exclude_id:
            continue

        existing = Event.from_dict(event)
        existing_start = existing.get_start_datetime()
        existing_end = existing.get_end_datetime()

        if new_start < existing_end and new_end > existing_start:
            conflicts.append(event)

    return conflicts


def add_event(
    title: str,
    date: str,
    time: str,
    duration: int,
    location: Optional[str] = None,
    description: Optional[str] = None,
    force: bool = False,
    *,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a new event with conflict detection"""
    if not title or not date or not time:
        raise ValueError("title, date, and time are required")

    if duration <= 0:
        raise ValueError("duration must be positive")

    parsed_date, parsed_time = _parse_date_time(date, time)
    events = load_events(db_path)
    now = _to_iso(datetime.now())

    event_id = _ensure_unique_id(events, _generate_short_id())
    event = Event(
        id=event_id,
        title=title.strip(),
        date=parsed_date,
        start_time=parsed_time,
        duration=duration,
        location=location.strip() if location else None,
        description=description.strip() if description else None,
        created=now,
        updated=now,
    )

    if not force:
        conflicts = _check_conflicts(events, event)
        if conflicts:
            conflict_details = []
            for c in conflicts:
                conflict_event = Event.from_dict(c)
                end_time = conflict_event.get_end_datetime().strftime("%H:%M")
                detail = (
                    f'"{c["title"]}" ' f"({conflict_event.start_time} - {end_time})"
                )
                conflict_details.append(detail)
            msg = (
                f"Event conflicts with {', '.join(conflict_details)}. "
                "Use --force to schedule anyway"
            )
            raise ValueError(msg)

    events.append(event.to_dict())
    events.sort(key=lambda e: (e["date"], e["start_time"]))
    save_events(events, db_path)

    return event.to_dict()


def list_events(
    *,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    today: bool = False,
    week: bool = False,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List events with filtering options"""
    events = load_events(db_path)

    if today:
        today_str = datetime.now().strftime("%Y-%m-%d")
        events = [e for e in events if e["date"] == today_str]
    elif week:
        now = datetime.now()
        days_until_sunday = 6 - now.weekday()
        week_end = now + timedelta(days=days_until_sunday)
        week_start = week_end - timedelta(days=6)

        week_start_str = week_start.strftime("%Y-%m-%d")
        week_end_str = week_end.strftime("%Y-%m-%d")

        events = [e for e in events if week_start_str <= e["date"] <= week_end_str]
    else:
        if from_date:
            parsed_from = parse_dt(from_date).strftime("%Y-%m-%d")
            events = [e for e in events if e["date"] >= parsed_from]
        if to_date:
            parsed_to = parse_dt(to_date).strftime("%Y-%m-%d")
            events = [e for e in events if e["date"] <= parsed_to]

        # Only apply "today onwards" filter if no explicit date filters
        if not from_date and not to_date and not today and not week:
            today_str = datetime.now().strftime("%Y-%m-%d")
            events = [e for e in events if e["date"] >= today_str]

    return events


def show_event(
    event_id: str, *, db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Show detailed information about a specific event"""
    events = load_events(db_path)

    for event in events:
        if event["id"] == event_id:
            event_obj = Event.from_dict(event)
            end_time = event_obj.get_end_datetime().strftime("%H:%M")
            conflicts = _check_conflicts(events, event_obj, exclude_id=event_id)

            result = event.copy()
            result["end_time"] = end_time
            result["conflicts"] = conflicts
            return result

    return None


def delete_event(
    event_id: str, *, db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Delete an event and return deleted event info"""
    events = load_events(db_path)

    for i, event in enumerate(events):
        if event["id"] == event_id:
            deleted_event = events.pop(i)
            save_events(events, db_path)
            return deleted_event

    return None


def delete_events_by_date(
    date: str, *, db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Delete all events on a specific date"""
    parsed_date = parse_dt(date).strftime("%Y-%m-%d")
    events = load_events(db_path)

    deleted_events = []
    remaining_events = []

    for event in events:
        if event["date"] == parsed_date:
            deleted_events.append(event)
        else:
            remaining_events.append(event)

    if deleted_events:
        save_events(remaining_events, db_path)

    return deleted_events


def edit_event(
    event_id: str,
    *,
    title: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    duration: Optional[int] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Edit an existing event"""
    events = load_events(db_path)

    for event in events:
        if event["id"] == event_id:
            updated_data = event.copy()

            if title is not None:
                updated_data["title"] = title.strip()
            if date is not None or time is not None:
                current_date = updated_data["date"]
                current_time = updated_data["start_time"]
                new_date = date if date else current_date
                new_time = time if time else current_time
                parsed_date, parsed_time = _parse_date_time(new_date, new_time)
                updated_data["date"] = parsed_date
                updated_data["start_time"] = parsed_time
            if duration is not None:
                if duration <= 0:
                    raise ValueError("duration must be positive")
                updated_data["duration"] = duration
            if location is not None:
                updated_data["location"] = location.strip() if location else None
            if description is not None:
                updated_data["description"] = (
                    description.strip() if description else None
                )

            updated_event = Event.from_dict(updated_data)
            conflicts = _check_conflicts(events, updated_event, exclude_id=event_id)
            if conflicts:
                conflict_details = []
                for c in conflicts:
                    conflict_event = Event.from_dict(c)
                    end_time = conflict_event.get_end_datetime().strftime("%H:%M")
                    detail = (
                        f'"{c["title"]}" ' f"({conflict_event.start_time} - {end_time})"
                    )
                    conflict_details.append(detail)
                msg = (
                    f"Edit would create conflicts with "
                    f"{', '.join(conflict_details)}"
                )
                raise ValueError(msg)

            # Ensure timestamp changes
            time_module.sleep(0.2)
            updated_data["updated"] = _to_iso(datetime.now())
            events[events.index(event)] = updated_data

            events.sort(key=lambda e: (e["date"], e["start_time"]))
            save_events(events, db_path)

            return updated_data

    return None


def search_events(
    query: str, title_only: bool = False, *, db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search events by title and/or description"""
    if not query.strip():
        return []

    q = query.strip().lower()
    events = load_events(db_path)

    results = []
    for event in events:
        if title_only:
            searchable = (event.get("title") or "").lower()
        else:
            fields = [
                event.get("title") or "",
                event.get("description") or "",
                event.get("location") or "",
            ]
            searchable = " ".join(fields).lower()

        if q in searchable:
            results.append(event)

    return results


def get_agenda(
    date: Optional[str] = None, week: bool = False, *, db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Get agenda view for a specific date or week """
    if week:
        events = list_events(week=True, db_path=db_path)
        agenda = {}
        for event in events:
            event_date = event["date"]
            if event_date not in agenda:
                agenda[event_date] = []
            agenda[event_date].append(event)

        return {"type": "week", "events_by_date": agenda, "total_events": len(events)}
    else:
        target_date = date if date else datetime.now().strftime("%Y-%m-%d")
        if date:
            target_date = parse_dt(date).strftime("%Y-%m-%d")

        events = [e for e in load_events(db_path) if e["date"] == target_date]

        return {
            "type": "day",
            "date": target_date,
            "events": events,
            "total_events": len(events),
        }
