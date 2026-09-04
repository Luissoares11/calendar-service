from fastapi import APIRouter, Depends, HTTPException, Query

from server.auth import verify_token
from app.models import EventCreate, EventUpdate, EventDelete
from app.features.calendar import add_event, delete_event, edit_event, list_events

router = APIRouter(prefix="/events", tags=["events"])


@router.post("")
def create_event(body: EventCreate, token: str = Depends(verify_token)):
    """
    Create a new event.

    Example:
    ```json
    {
      "action": "add",
      "title": "University Meeting",
      "type": "meeting",
      "date": "2026-09-05",
      "time": "14:30",
      "notes": "Discuss project plans",
      "recurrence": "none"
    }
    ```
    """
    result = add_event(
        title=body.title,
        date_str=body.date,
        time_str=body.time,
        event_type=body.type,
        notes=body.notes,
        recurrence=body.recurrence or "none",
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("")
def get_events(
    list: bool = Query(True, alias="list"),
    days: int = Query(30, description="Number of days ahead to fetch"),
    past: bool = Query(False, description="Include past events"),
    all: bool = Query(False, description="Get all events"),
    token: str = Depends(verify_token)
):
    """
    List events with flexible filtering.

    Query parameters:
    - `list=true` — enable listing (required)
    - `days=30` — look ahead this many days (default 30)
    - `past=true` — show past events instead
    - `all=true` — show all events (ignores date filters)

    Example: `/events?list=true&days=7`
    """
    if not list:
        raise HTTPException(status_code=400, detail="list parameter is required")

    result = list_events(
        days_ahead=days,
        include_past=past,
        all_events=all
    )

    return result


@router.post("/edit")
def update_event(body: EventUpdate, token: str = Depends(verify_token)):
    """
    Update an existing event.

    Example:
    ```json
    {
      "action": "edit",
      "title": "University Meeting",
      "new_title": "Updated Meeting",
      "new_date": "2026-09-06",
      "new_time": "15:00"
    }
    ```
    """
    result = edit_event(
        title=body.title,
        new_title=body.new_title,
        new_date_str=body.new_date,
        new_time_str=body.new_time,
        new_notes=body.new_notes,
        new_type=body.new_type,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/delete")
def remove_event(body: EventDelete, token: str = Depends(verify_token)):
    """
    Delete an event by title.

    Example:
    ```json
    {
      "action": "delete",
      "title": "University Meeting"
    }
    ```
    """
    result = delete_event(body.title)

    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])

    return result


@router.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "calendar"}
