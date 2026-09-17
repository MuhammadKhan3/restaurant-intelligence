import type {
  CameraEvent,
  CameraStatus,
  EntranceEvent,
  QueueEvent,
  TableEvent,
  TableStatus,
} from "@/types/events";

const TABLE_STATE_STYLES: Record<string, string> = {
  available: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  occupied: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  cleaning: "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300",
  blocked: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  unknown: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
};

export function tableStateStyle(state: string): string {
  return TABLE_STATE_STYLES[state] ?? TABLE_STATE_STYLES.unknown;
}

const CAMERA_STATUS_STYLES: Record<string, string> = {
  connected: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  connecting: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  disconnected: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  error: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
};

export function cameraStatusStyle(status: string): string {
  return CAMERA_STATUS_STYLES[status] ?? CAMERA_STATUS_STYLES.disconnected;
}

/** Reduce a table's event history down to its current state: the most recent event's `to_state`. */
export function deriveTableStatuses(events: TableEvent[]): TableStatus[] {
  const latestByZone = new Map<string, TableEvent>();

  for (const event of events) {
    const existing = latestByZone.get(event.zone_id);
    if (!existing || event.occurred_at > existing.occurred_at) {
      latestByZone.set(event.zone_id, event);
    }
  }

  return Array.from(latestByZone.values())
    .map((event) => ({ zoneId: event.zone_id, state: event.to_state, since: event.occurred_at }))
    .sort((a, b) => a.zoneId.localeCompare(b.zoneId));
}

/** Reduce a camera's event history down to its current status: the most recent event's `status`. */
export function deriveCameraStatuses(events: CameraEvent[]): CameraStatus[] {
  const latestByCamera = new Map<string, CameraEvent>();

  for (const event of events) {
    const existing = latestByCamera.get(event.camera_id);
    if (!existing || event.occurred_at > existing.occurred_at) {
      latestByCamera.set(event.camera_id, event);
    }
  }

  return Array.from(latestByCamera.values())
    .map((event) => ({
      cameraId: event.camera_id,
      status: event.status,
      since: event.occurred_at,
    }))
    .sort((a, b) => a.cameraId.localeCompare(b.cameraId));
}

function netEntries(events: { event_type: "entry" | "exit" }[]): number {
  const count = events.reduce(
    (total, event) => total + (event.event_type === "entry" ? 1 : -1),
    0,
  );
  return Math.max(0, count);
}

/** Current customer count: entries minus exits across all entrance zones, floored at zero. */
export function deriveCustomerCount(events: EntranceEvent[]): number {
  return netEntries(events);
}

/** Current waiting count: joins minus leaves across all queue zones, floored at zero. */
export function deriveWaitingCount(events: QueueEvent[]): number {
  return netEntries(events);
}
