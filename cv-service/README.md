# CV Service — Restaurant Queue & Table Intelligence

Foundation for the computer-vision service: configuration, logging, a test
suite, a camera abstraction layer, YOLO-based person detection, person
tracking, table zone configuration, and a FastAPI app exposing detection. No
queue detection or table-occupancy/turnover logic yet.

## Camera module (`app/camera/`)

- `VideoSource` — common interface (`connect`, `read`, `release`, `status`).
- `LocalVideoFileSource`, `WebcamSource`, `RTSPCameraSource` — OpenCV
  `VideoCapture`-backed implementations for each source type.
- `ConnectionStatus` — `disconnected` / `connecting` / `connected` / `error`.
- `FrameProcessingPipeline` — pulls frames from a `VideoSource` through an
  ordered list of processor callables (none registered yet).
- `create_video_source(settings)` — builds the source configured via
  `VIDEO_SOURCE_TYPE` / `VIDEO_SOURCE` in `.env`.

## Detection module (`app/detection/`)

- `YOLOModelLoader` — lazily loads and caches a YOLO model (`YOLO_MODEL`).
- `PersonDetector` — runs the model, filters to the "person" class, applies
  `CONFIDENCE_THRESHOLD`.
- `Detection` — bounding box + confidence + class id/name.
- `draw_detections(frame, detections)` — draws bounding boxes and labels for
  visualization.
- `create_person_detector(settings)` — builds a `PersonDetector` from config.

## Tracking module (`app/tracking/`)

- `Tracker` — common interface (`update(frame)`, `reset()`).
- `ByteTracker` — YOLO + ByteTrack (via ultralytics' built-in `model.track`),
  assigns persistent IDs across frames.
- `Track` — one frame's tracked box (id, bbox, confidence, class).
- `TrackLifecycleManager` — keeps a track `ACTIVE` while seen, marks it
  `LOST` on brief gaps, and `REMOVED` after `max_lost_frames` consecutive
  misses.
- `draw_tracks(frame, tracks)` — draws boxes with a per-ID color and label.
- `create_person_tracker(settings)` — builds a `ByteTracker` from config.

## Tables module (`app/tables/`)

- `TableZone` — a table's polygon zone (id, name, capacity, points);
  validates `capacity >= 1` and `points` forming a polygon (>= 3 points).
- `TableZoneStore` — create/get/list/update/delete table zones in memory,
  plus `save(file_path)` / `load(file_path)` to persist as JSON
  (`TABLE_ZONES_FILE` in `.env`; no database yet). Exposed over HTTP via
  `app/routes/table_zones.py` (see API section below).
- `draw_table_zones(frame, zones)` — draws each zone's polygon and label.

- `app/tables/state.py` — `TableStateManager`: debounced AVAILABLE/OCCUPIED
  transitions from occupancy results, plus manual CLEANING/BLOCKED overrides
  and per-zone `StateChange` history.
- `app/tables/timing.py` — `TableTimingTracker`: opens/closes a `TableSession`
  off of `StateChange` events, and flags long-running occupied sessions.

## Sessions module (`app/sessions/`)

Anonymous, continuous customer/table session tracking — no name, face, or
other identity is ever attached, just ephemeral tracker ids scoped to one
visit.

- `CustomerSession` — an anonymous group's dining session: `zone_id`,
  `started_at`/`ended_at`, `track_ids` (every tracker id ever part of the
  group this visit), `peak_customer_count`, `status` (ACTIVE/COMPLETED).
- `TableSessionTracker.update(zone_id, assigned_track_ids, now)` — call once
  per tick per zone. A zone going from no session to having assigned tracks
  starts a new session (a new group); one that stays empty for
  `empty_grace_period` (wall-clock time, not frame count) ends the session.
  `current_customer_count()` is the live count (0 during a grace-period gap);
  `current_session(zone_id).peak_customer_count` is the group's representative
  size for display.

This composes with — rather than replaces — Phases 4/6/7/8: feed it
`TrackLifecycleManager`'s output (ACTIVE + LOST, not just `active_tracks()`)
through `assign_people_to_tables` each tick. Two independent grace mechanisms
then make brief occlusion non-disruptive: `TrackLifecycleManager` keeps an
occluded individual's track alive at its last position (`max_lost_frames`,
Phase 4), and `TableSessionTracker` additionally tolerates the whole zone
reading empty for `empty_grace_period` before deciding the group actually
left. Detecting a group swap *without* the table ever reading empty (e.g. a
fast handoff) is a known, intentional gap — solving it would require
re-identifying individuals, which this feature explicitly avoids.

## Entrance module (`app/entrance/`)

- `EntranceZone` — a doorway split into adjacent `outside`/`inside` polygons.
- `EntranceTracker` — compares each track's polygon side frame-to-frame;
  outside→inside is an `EntranceEvent(ENTRY)`, the reverse is `EXIT`.
- `CustomerCounter` — running customer count from a stream of entrance
  events, clamped at zero.

## Queue module (`app/queue/`)

- `QueueZone` — a single polygon marking the waiting area.
- `QueueTracker` — entering the polygon is a `QueueEvent(ENTRY)`, leaving is
  `EXIT`; `current_count` is the number currently waiting.
  `remove_track(track_id)` forces an `EXIT` for a track tracking has
  permanently lost, so it doesn't stay counted forever.
- `estimate_groups(tracks, max_distance)` — clusters waiting people into
  probable parties by transitive proximity of their center points.
- `QueueTimingTracker` — opens/closes a `QueueWait` per person off of
  `QueueEvent`s; `average_waiting_time()` / `maximum_waiting_time()` summarize
  completed waits, and `abandoned_waits(threshold)` flags people who left
  after waiting past `threshold` (a proxy for "gave up," since this tracker
  alone can't tell whether they were actually seated).

## Assignment module (`app/assignment/`)

- `find_available_tables(zones, table_states)` / `match_table_for_group(size,
  zones)` — filter to AVAILABLE tables, then pick the smallest one that fits a
  group.
- `TableAssignmentService` — `assign()` matches a group to a free table
  (WALKING); `confirm_seated()` transitions it to SEATED once occupancy
  confirms it; `release()` frees the table again. A table with an active
  assignment is excluded from further matching even if occupancy detection
  hasn't caught up yet.

## Wait-time module (`app/waittime/`)

- `WaitTimeEstimator` — combines current capacity matching (reusing
  `app/assignment/matcher.py`) with historical turnover from
  `TableTimingTracker` (Phase 8) to estimate a group's wait: zero if a table
  is free now, otherwise the remaining time on whichever eligible occupied
  table is closest to its average turnover. Falls back to a configurable
  default turnover with no history or no occupied/available candidates.

## Analytics module (`app/analytics/`)

- `analyze_table(zone_id, sessions, period)` — session count, average/total
  duration, turnover per day, and utilization (fraction of `period` occupied,
  capped at 1.0), from `TableTimingTracker` (Phase 8) session history.
- `peak_occupancy(sessions)` — max number of tables occupied at the same
  instant, via a sweep over session start/end events.
- `hourly_metrics()` / `daily_metrics()` — one `PeriodMetric` per hour/day
  bucket, splitting a session's occupied time proportionally across the
  buckets it spans.

## Alerts module (`app/alerts/`)

- `detect_long_queue_alert` / `detect_long_wait_alert` /
  `detect_long_occupancy_alert` / `detect_camera_offline_alert` /
  `detect_unknown_table_alert` — pure threshold checks; each returns a draft
  `Alert` (empty `id`) or `None`. `detect_long_occupancy_alert` reuses
  `TableTimingTracker.is_long_occupancy()` directly.
- `AlertManager` — `raise_alert()` assigns the real id and dedupes so a
  persistent condition doesn't spam duplicates (only one active alert per
  type+subject); `active_alerts()` is the "Alert Dashboard" data;
  `acknowledge(alert_id)` clears it from the dashboard into history.

## API (`app/routes/`, `app/services/`, `app/models/`)

FastAPI app (`app/main.py`), created at startup with a cached `PersonDetector`
in `app.state`:

- `GET /health` — liveness check.
- `GET /detections` — reads one frame from the configured video source and
  returns person detections; `503` if the source can't produce a frame.
- `GET/POST /table-zones`, `GET/PUT/DELETE /table-zones/{zone_id}` — CRUD over
  table zones, backed by `TableZoneStore`. Loaded from `TABLE_ZONES_FILE` at
  startup; every write re-saves the whole store back to that file.

`app/services/detection_service.py` wires the camera and detection modules
together; `app/models/detection.py` defines the API response schema.

`app/services/backend_client.py` — `BackendEventForwarder` POSTs table/camera/
entrance/queue events to the `backend` service (`BACKEND_URL` in `.env`); a
forwarding failure is logged and swallowed rather than raised. Nothing calls
it automatically yet — there's no continuous camera-processing loop tying
detection → tracking → tables/entrance/queue → forwarding together across
frames, only the single-frame `/detections` endpoint. Wiring that loop up is
separate, still-unstarted work.

## Setup

```bash
uv sync
```

## Environment

```bash
cp .env.example .env
```

On Windows, if `cp` is unavailable, copy `.env.example` to `.env` manually
(or create `.env` with the same contents).

## Run

```bash
uv run python -m app.main
```

Serves the API at http://localhost:8000 (docs at `/docs`).

## Test

```bash
uv run pytest
```

## Lint

```bash
uv run ruff check .
```

## Format

```bash
uv run ruff format .
```
