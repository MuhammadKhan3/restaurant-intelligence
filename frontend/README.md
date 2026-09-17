# Frontend — Restaurant Queue & Table Intelligence

Next.js dashboard. Shows a live floor view (table status cards with
occupancy timers, camera status) polling `backend`'s event API every 5s.
No authentication or analytics/alerts pages yet.

## Requirements

```text
Node.js 20.9+
pnpm
```

## Install

```bash
pnpm install
```

## Environment

Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

## Development

```bash
pnpm dev
```

Runs at [http://localhost:3000](http://localhost:3000).

## Build

```bash
pnpm build
```

## Start production build

```bash
pnpm start
```

## Lint

```bash
pnpm lint
```

## Structure

```text
frontend/
├── app/                    App Router entry (root layout, floor view page, global styles)
├── components/dashboard/   AppShell, Navigation, FloorView, TableStatusCard, OccupancyTimer, CameraStatusList
├── lib/                    api.ts (backend fetches), status.ts (derive current status from event history)
├── types/                  Shared TypeScript types (events.ts)
└── public/                 Static assets
```

The floor view has no source of table zone metadata (names/capacity) yet —
`cv-service`'s `TableZoneStore` isn't exposed over an API — so each table is
identified by its `zone_id` and its state is derived from the most recent
`backend` table event for that zone. A zone with no events yet simply won't
appear until `backend` records one.

Requires `backend` running at `NEXT_PUBLIC_API_URL` (default
`http://localhost:4000`).
