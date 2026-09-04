from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EventCreate(BaseModel):
    """Model for creating an event."""
    action: str = Field(..., description="Action type: 'add'")
    title: str = Field(..., description="Event title")
    type: str = Field(default="other", description="Event type: exam, test, appointment, etc.")
    date: str = Field(..., description="Event date (DD/MM/YYYY or YYYY-MM-DD)")
    time: str = Field(default="09:00", description="Event time (HH:MM)")
    notes: str = Field(default="", description="Event notes")
    recurrence: Optional[str] = Field(default=None, description="Recurrence: yearly, monthly, weekly, or none")


class EventUpdate(BaseModel):
    """Model for updating an event."""
    action: str = Field(..., description="Action type: 'edit'")
    title: str = Field(..., description="Event title to search for")
    new_title: Optional[str] = Field(default=None)
    new_date: Optional[str] = Field(default=None)
    new_time: Optional[str] = Field(default=None)
    new_notes: Optional[str] = Field(default=None)
    new_type: Optional[str] = Field(default=None)


class EventDelete(BaseModel):
    """Model for deleting an event."""
    action: str = Field(..., description="Action type: 'delete'")
    title: str = Field(..., description="Event title to search for")


class Event(BaseModel):
    """Model for an event response."""
    id: str
    title: str
    type: str
    start_time: str
    end_time: str
    notes: str
    recurrence: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Model for listing events."""
    events: list[Event]
    total: int
