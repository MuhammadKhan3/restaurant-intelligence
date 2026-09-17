# Backend — Restaurant Queue & Table Intelligence

FastAPI service that ingests CV events from `cv-service` and persists them to
PostgreSQL. Table/camera event ingestion and history only so far — no
restaurant-metrics or AI endpoints yet.

## API (`app/routes/`, `app/services/`, `app/models/`, `app/schemas/`)

- `GET /health` — liveness check.
- `POST /events/tables` — record a table state transition (`zone_id`,
  `from_state`, `to_state`, `occurred_at`).
- `GET /events/tables` — list recorded table events, optionally filtered by
  `zone_id`, newest first (`limit`, default 100, max 1000).
- `POST /events/cameras` — record a camera connection status change
  (`camera_id`, `status`, `occurred_at`).
- `GET /events/cameras` — list recorded camera events, optionally filtered by
  `camera_id`, newest first.

`app/db.py` builds a SQLAlchemy session factory from `DATABASE_URL` and
creates tables on startup (no migration tool yet). `app/services/event_service.py`
wires the ORM models to the API.

## Setup

```bash
uv sync
```

## Environment

```bash
cp .env.example .env
```

On Windows, if `cp` is unavailable, copy `.env.example` to `.env` manually
(or create `.env` with the same contents). Requires a running PostgreSQL
instance matching `DATABASE_URL`.

## Run

```bash
uv run python -m app.main
```

Serves the API at http://localhost:4000 (docs at `/docs`), matching
`frontend`'s `NEXT_PUBLIC_API_URL`.

## Test

```bash
uv run pytest
```

Tests run against an in-memory SQLite database, not PostgreSQL.

## Lint

```bash
uv run ruff check .
```

## Format

```bash
uv run ruff format .
```
