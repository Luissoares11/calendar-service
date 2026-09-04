# Calendar Service

A standalone microservice for managing calendar events, built to work with the EDITH AI orchestrator.

## Features

- ✅ Create, read, update, and delete events
- ✅ Support for event types (meeting, exam, appointment, etc.)
- ✅ Recurring events (yearly, monthly, weekly)
- ✅ Event notes and timestamps
- ✅ Simple REST API

## Quick Start

### Requirements

- Python 3.12+
- Docker + Docker Compose (optional, for containerized runs)

### Setup

```bash
git clone https://github.com/Luissoares11/calendar-service
cd calendar-service
pip install -r requirements.txt
cp .env  # fill in your config
```

### Environment Variables

```env
CALENDAR_API_TOKEN=your_secret_token
TIMEZONE=Europe/Lisbon
DATABASE_PATH=data/calendar.db
```

### Running Locally (Python)

```bash
python -m uvicorn server.main:app --host 0.0.0.0 --port 8010
```

### Running Locally (Docker)

```bash
docker compose build
docker compose up -d
```

## API Reference

### Base URL

```
http://localhost:8010
```

### Authentication

All endpoints (except `/health`) require a Bearer token:

```
Authorization: Bearer <CALENDAR_API_TOKEN>
```

### Endpoints

#### `GET /health`

Health check (no auth required).

**Response:**

```json
{
  "status": "ok",
  "service": "calendar"
}
```

#### `POST /events`

Create a new event.

**Request:**

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

**Response:**

```json
{
  "success": true,
  "event_id": "uuid-here",
  "message": "Added 💼 Meeting 'University Meeting' on 05 Sep at 14:30."
}
```

#### `GET /events?list=true&days=30`

List upcoming events.

**Query Parameters:**

- `list=true` — Required. Enable listing.
- `days=30` — Look ahead this many days (default: 30).
- `past=true` — Show past events instead of upcoming.
- `all=true` — Show all events (ignores date filters).

**Response:**

```json
{
  "success": true,
  "events": [
    {
      "id": "event-uuid",
      "title": "University Meeting",
      "type": "meeting",
      "type_label": "💼 Meeting",
      "start_time": "2026-09-05T14:30:00+01:00",
      "end_time": "2026-09-05T15:30:00+01:00",
      "notes": "Discuss project plans",
      "recurrence": null,
      "created_at": "2026-09-04T10:00:00"
    }
  ],
  "total": 1,
  "message": "Found 1 event(s)."
}
```

#### `POST /events/edit`

Update an existing event.

**Request:**

```json
{
  "action": "edit",
  "title": "University Meeting",
  "new_title": "Updated Meeting",
  "new_date": "2026-09-06",
  "new_time": "15:00"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Updated event 'Updated Meeting'."
}
```

#### `POST /events/delete`

Delete an event by title (fuzzy match).

**Request:**

```json
{
  "action": "delete",
  "title": "University Meeting"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Removed event 'University Meeting'."
}
```

## Event Types

Supported event types (with emoji):

- `exam` — 🎓 Exam
- `appointment` — 🏥 Appointment
- `birthday` — 🎂 Birthday
- `meeting` — 💼 Meeting
- `deadline` — ⚠️ Deadline
- `other` — 📅 Event

## Date Formats

Supported date formats:

- `DD/MM/YYYY` (e.g., `05/09/2026`)
- `YYYY-MM-DD` (e.g., `2026-09-05`)
- `DD-MM-YYYY` (e.g., `05-09-2026`)

Time format: `HH:MM` (e.g., `14:30`)

## Development

### Running Tests

```bash
pytest tests/ -v
```

All tests pass ✅ (10/10)

Tests cover:
- ✅ `created_at` field in event responses
- ✅ Monthly recurrence calculation
- ✅ Leap year handling for Feb 29
- ✅ Event CRUD operations
- ✅ Integration workflows

### Project Structure

```
calendar-service/
├── app/
│   ├── database.py          # SQLite setup & connection
│   ├── utils.py             # Helper functions
│   ├── models.py            # Pydantic models
│   └── features/
│       └── calendar.py      # Calendar business logic
├── server/
│   ├── main.py              # FastAPI app
│   ├── auth.py              # Token verification
│   └── routers/
│       └── events.py        # Event endpoints
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Future Work

- [ ] Event reminders and notifications
- [ ] Recurring event exceptions (skip specific occurrences)
- [ ] Event attachments/links

## License

MIT
