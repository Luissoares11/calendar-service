import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import sqlite3
import tempfile

# Set test database
test_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
os.environ["DATABASE_PATH"] = test_db.name

from app.database import init_db, _conn
from app.features.calendar import add_event, list_events, delete_event, edit_event, _next_occurrence
from app.utils import TIMEZONE


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Initialize fresh database for each test."""
    init_db()
    yield
    # Cleanup
    with _conn() as con:
        con.execute("DELETE FROM events")


class TestListEvents:
    """Test list_events() with created_at field."""

    def test_list_events_includes_created_at(self):
        """Test that list_events returns created_at without crashing."""
        # Add an event
        add_event("Team Meeting", "25/09/2026", "10:00", "meeting", "Quarterly sync")

        # List events should not crash and include created_at
        result = list_events(days_ahead=30)

        assert result["success"] is True
        assert len(result["events"]) == 1
        assert "created_at" in result["events"][0]
        assert result["events"][0]["created_at"] is not None
        print(f"✓ created_at field present: {result['events'][0]['created_at']}")

    def test_list_events_multiple_events(self):
        """Test list_events with multiple events all have created_at."""
        add_event("Meeting 1", "25/09/2026", "09:00", "meeting")
        add_event("Exam", "26/09/2026", "14:00", "exam")
        add_event("Birthday", "27/09/2026", "00:00", "birthday")

        result = list_events(days_ahead=30)

        assert result["success"] is True
        assert len(result["events"]) == 3
        for event in result["events"]:
            assert "created_at" in event
            assert event["created_at"] is not None
        print(f"✓ All {len(result['events'])} events have created_at")


class TestMonthlyRecurrence:
    """Test monthly recurrence calculation fix."""

    def test_monthly_recurrence_forward_in_same_month(self):
        """Test monthly recurrence from day in past to future day in same month."""
        # Dec 15 event, checking from Jan 10 (before Jan 15)
        dt_event = datetime(2024, 12, 15, 10, 0)
        now = datetime(2025, 1, 10, 12, 0)

        next_occ = _next_occurrence(dt_event, "monthly", now)

        # Should be Jan 15 (next month occurrence)
        assert next_occ.month == 1
        assert next_occ.day == 15
        assert next_occ.year == 2025
        print(f"✓ Dec 15 → Jan 10 correctly returns Jan 15")

    def test_monthly_recurrence_year_rollover(self):
        """Test monthly recurrence that crosses year boundary."""
        dt_event = datetime(2024, 12, 20, 10, 0)
        now = datetime(2025, 1, 10, 12, 0)

        next_occ = _next_occurrence(dt_event, "monthly", now)

        # Should be Jan 20 (next month)
        assert next_occ.month == 1
        assert next_occ.day == 20
        assert next_occ.year == 2025
        print(f"✓ Dec 20 → Jan 10 correctly returns Jan 20 (year rollover handled)")

    def test_monthly_recurrence_multiple_jumps(self):
        """Test monthly recurrence with multiple month jumps."""
        dt_event = datetime(2024, 1, 15, 10, 0)
        now = datetime(2025, 4, 20, 12, 0)

        next_occ = _next_occurrence(dt_event, "monthly", now)

        # Should be May 15 (next month occurrence after April 20)
        assert next_occ.month == 5
        assert next_occ.day == 15
        assert next_occ.year == 2025
        print(f"✓ Multiple month jump: Jan 15 → Apr 20 correctly returns May 15")

    def test_monthly_recurrence_day_overflow(self):
        """Test monthly recurrence with day overflow (e.g., Jan 31 → Feb 28)."""
        dt_event = datetime(2024, 1, 31, 10, 0)
        now = datetime(2025, 2, 5, 12, 0)

        next_occ = _next_occurrence(dt_event, "monthly", now)

        # Should handle gracefully, falling back to Feb 28 (not crash)
        assert next_occ.month == 2
        assert next_occ.day == 28  # Fallback for non-existent Feb 31
        print(f"✓ Day overflow handled: Jan 31 → Feb correctly returns Feb 28")


class TestLeapYearRecurrence:
    """Test yearly recurrence with leap year dates (Feb 29)."""

    def test_yearly_recurrence_leap_to_non_leap(self):
        """Test Feb 29 event with yearly recurrence advancing to non-leap year."""
        dt_event = datetime(2024, 2, 29, 10, 0)  # Leap year
        now = datetime(2025, 2, 15, 12, 0)  # Before Feb 28 in non-leap year

        # Should not crash and gracefully handle
        next_occ = _next_occurrence(dt_event, "yearly", now)

        assert next_occ.year == 2025
        assert next_occ.month == 2
        assert next_occ.day == 28  # Fallback to Feb 28
        print(f"✓ Feb 29 (leap) → 2025 correctly returns Feb 28 (non-leap)")

    def test_yearly_recurrence_leap_year_cycle(self):
        """Test Feb 29 cycling through leap and non-leap years."""
        dt_event = datetime(2024, 2, 29, 10, 0)
        now = datetime(2028, 3, 1, 12, 0)  # 2028 is a leap year

        next_occ = _next_occurrence(dt_event, "yearly", now)

        # Should be 2029 (non-leap) with fallback to Feb 28
        assert next_occ.year == 2029
        assert next_occ.month == 2
        assert next_occ.day == 28
        print(f"✓ Feb 29 yearly recurrence through leap years handled correctly")


class TestIntegration:
    """Integration tests for full workflow."""

    def test_add_and_list_with_all_fields(self):
        """Test adding event and listing returns all fields including created_at."""
        result = add_event(
            title="Project Deadline",
            date_str="30/09/2026",
            time_str="17:00",
            event_type="deadline",
            notes="Q3 milestone",
            recurrence="monthly"
        )

        assert result["success"] is True
        event_id = result["event_id"]

        # List and verify all fields
        list_result = list_events(days_ahead=30)
        assert list_result["success"] is True
        assert len(list_result["events"]) == 1

        event = list_result["events"][0]
        assert event["id"] == event_id
        assert event["title"] == "Project Deadline"
        assert event["type"] == "deadline"
        assert event["recurrence"] == "monthly"
        assert event["created_at"] is not None
        print(f"✓ Full integration test passed: all fields present and correct")

    def test_recurring_event_in_list(self):
        """Test that recurring events appear correctly in list."""
        # Add event from past
        result = add_event(
            title="Monthly Standup",
            date_str="05/08/2026",  # In the past
            time_str="10:00",
            event_type="meeting",
            recurrence="monthly"
        )

        assert result["success"] is True

        # List should show it in the next 30 days with updated date
        list_result = list_events(days_ahead=30)
        assert list_result["success"] is True
        assert len(list_result["events"]) > 0
        print(f"✓ Recurring event correctly appears in future dates")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
