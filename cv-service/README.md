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
  (`TABLE_ZONES_FILE` in `.env`; no database yet).
- `draw_table_zones(frame, zones)` — draws each zone's polygon and label.

- `app/tables/state.py` — `TableStateManager`: debounced AVAILABLE/OCCUPIED
  transitions from occupancy results, plus manual CLEANING/BLOCKED overrides
  and per-zone `StateChange` history.
- `app/tables/timing.py` — `TableTimingTracker`: opens/closes a `TableSession`
  off of `StateChange` events, and flags long-running occupied sessions.

## Entrance module (`app/entrance/`)

- `EntranceZone` — a doorway split into adjacent `outside`/`inside` polygons.
- `EntranceTracker` — compares each track's polygon side frame-to-frame;
  outside→inside is an `EntranceEvent(ENTRY)`, the reverse is `EXIT`.
- `CustomerCounter` — running customer count from a stream of entrance
  events, clamped at zero.

## API (`app/routes/`, `app/services/`, `app/models/`)

FastAPI app (`app/main.py`), created at startup with a cached `PersonDetector`
in `app.state`:

- `GET /health` — liveness check.
- `GET /detections` — reads one frame from the configured video source and
  returns person detections; `503` if the source can't produce a frame.

`app/services/detection_service.py` wires the camera and detection modules
together; `app/models/detection.py` defines the API response schema.

`app/services/backend_client.py` — `BackendEventForwarder` POSTs table/camera/
entrance events to the `backend` service (`BACKEND_URL` in `.env`); a
forwarding failure is logged and swallowed rather than raised. Nothing calls
it automatically yet — there's no continuous camera-processing loop tying
detection → tracking → tables/entrance → forwarding together across frames,
only the single-frame `/detections` endpoint. Wiring that loop up is separate,
still-unstarted work.

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
