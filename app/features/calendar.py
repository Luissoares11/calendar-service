import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.database import _conn
from app.utils import _now, _parse_datetime, TIMEZONE


# ── event types ───────────────────────────────────────────────

EVENT_TYPES = {
    "exam":        "🎓 Exam",
    "appointment": "🏥 Appointment",
    "birthday":    "🎂 Birthday",
    "meeting":     "💼 Meeting",
    "deadline":    "⚠️ Deadline",
    "other":       "📅 Event",
}


# ── calendar ──────────────────────────────────────────────────

def add_event(
    title: str,
    date_str: str,
    time_str: str = "09:00",
    event_type: str = "other",
    notes: str = "",
    recurrence: str = "none",
) -> dict:
    """
    Add a new event to the calendar.

    Returns a dict with the event ID and confirmation message.
    """
    try:
        dt = _parse_datetime(date_str, time_str)
        dt_end = dt + timedelta(hours=1)
        event_id = str(uuid.uuid4())
        recurrence_value = recurrence if recurrence in ("yearly", "monthly", "weekly") else None

        with _conn() as con:
            con.execute(
                "INSERT INTO events (id, title, type, start_time, end_time, notes, recurrence) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    event_id,
                    title,
                    event_type.lower(),
                    dt.isoformat(),
                    dt_end.isoformat(),
                    notes,
                    recurrence_value,
                )
            )

        suffix = f" (repeats {recurrence_value})" if recurrence_value else ""
        return {
            "success": True,
            "event_id": event_id,
            "message": f"Added {EVENT_TYPES.get(event_type.lower(), '📅 Event')} '{title}' on {dt.strftime('%d %b at %H:%M')}{suffix}."
        }
    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": f"I couldn't add that event: {e}"}


def delete_event(title: str) -> dict:
    """Delete an event by title (fuzzy match)."""
    try:
        with _conn() as con:
            row = con.execute(
                "SELECT id, title FROM events WHERE title LIKE ?",
                (f"%{title}%",)
            ).fetchone()
            if row:
                con.execute("DELETE FROM events WHERE id = ?", (row["id"],))
                return {"success": True, "message": f"Removed event '{row['title']}'."}
        return {"success": False, "message": "I couldn't find that event."}
    except Exception as e:
        return {"success": False, "message": f"Error deleting event: {e}"}


def edit_event(
    title: str,
    new_title: str = None,
    new_date_str: str = None,
    new_time_str: str = None,
    new_notes: str = None,
    new_type: str = None,
) -> dict:
    """Edit an existing event."""
    try:
        with _conn() as con:
            row = con.execute(
                "SELECT id, title, type, start_time, end_time, notes FROM events WHERE title LIKE ?",
                (f"%{title}%",)
            ).fetchone()

            if not row:
                return {"success": False, "message": "I couldn't find that event."}

            current_dt = datetime.fromisoformat(row["start_time"])

            if new_date_str or new_time_str:
                date_str = new_date_str or current_dt.strftime("%d/%m/%Y")
                time_str = new_time_str or current_dt.strftime("%H:%M")
                new_dt = _parse_datetime(date_str, time_str)
                new_dt_end = new_dt + timedelta(hours=1)
            else:
                new_dt = current_dt
                new_dt_end = datetime.fromisoformat(row["end_time"])

            final_title = new_title if new_title else row["title"]
            final_notes = new_notes if new_notes is not None else row["notes"]
            final_type = new_type.lower() if new_type else row["type"]

            con.execute(
                "UPDATE events SET title = ?, type = ?, start_time = ?, end_time = ?, notes = ? WHERE id = ?",
                (final_title, final_type, new_dt.isoformat(), new_dt_end.isoformat(), final_notes, row["id"])
            )

        return {"success": True, "message": f"Updated event '{final_title}'."}
    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": f"I couldn't update that event: {e}"}


def _next_occurrence(dt: datetime, recurrence: str, now: datetime) -> datetime:
    """Roll a recurring event's date forward to its next occurrence on/after `now`."""
    occ = dt
    if recurrence == "yearly":
        while occ < now:
            try:
                occ = occ.replace(year=occ.year + 1)
            except ValueError:
                # Handle leap year dates (Feb 29)
                occ = occ.replace(year=occ.year + 1, day=28)
    elif recurrence == "monthly":
        while occ < now:
            # Advance to next month
            if occ.month == 12:
                next_year = occ.year + 1
                next_month = 1
            else:
                next_year = occ.year
                next_month = occ.month + 1

            try:
                occ = occ.replace(year=next_year, month=next_month)
            except ValueError:
                # Handle day overflow (e.g., Jan 31 -> Feb 31 doesn't exist)
                occ = occ.replace(year=next_year, month=next_month, day=28)
    elif recurrence == "weekly":
        while occ < now:
            occ = occ + timedelta(weeks=1)
    return occ


def list_events(days_ahead: int = 30, include_past: bool = False, all_events: bool = False) -> dict:
    """
    List events with flexible filtering.

    - days_ahead: number of days to look ahead (default 30)
    - include_past: if True, show past events instead of future
    - all_events: if True, ignore date filters and show everything
    """
    now = _now()
    until = now + timedelta(days=days_ahead)

    with _conn() as con:
        rows = con.execute(
            "SELECT id, title, type, start_time, end_time, notes, recurrence, created_at FROM events ORDER BY start_time"
        ).fetchall()

    def effective_dt(row):
        dt = datetime.fromisoformat(row["start_time"])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo(TIMEZONE))
        if row["recurrence"] and dt < now:
            dt = _next_occurrence(dt, row["recurrence"], now)
        return dt

    if all_events:
        display = [(row, datetime.fromisoformat(row["start_time"])) for row in rows]
    elif include_past:
        filtered = []
        for row in rows:
            dt = effective_dt(row)
            orig = datetime.fromisoformat(row["start_time"])
            if orig.tzinfo is None:
                orig = orig.replace(tzinfo=ZoneInfo(TIMEZONE))
            if orig < now and not row["recurrence"]:
                filtered.append((row, orig))
        filtered.sort(key=lambda x: x[1], reverse=True)
        display = filtered[:20]
    else:
        filtered = []
        for row in rows:
            dt = effective_dt(row)
            if now <= dt <= until:
                filtered.append((row, dt))
        filtered.sort(key=lambda x: x[1])
        display = filtered

    if not display:
        if include_past:
            return {"success": True, "events": [], "message": "No past events found."}
        if all_events:
            return {"success": True, "events": [], "message": "No events found."}
        return {"success": True, "events": [], "message": f"No events in the next {days_ahead} days."}

    events = []
    for row, dt in display:
        events.append({
            "id": row["id"],
            "title": row["title"],
            "type": row["type"],
            "type_label": EVENT_TYPES.get(row["type"], "📅 Event"),
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "notes": row["notes"],
            "recurrence": row["recurrence"],
            "created_at": row["created_at"]
        })

    return {
        "success": True,
        "events": events,
        "total": len(events),
        "message": f"Found {len(events)} event(s)."
    }
