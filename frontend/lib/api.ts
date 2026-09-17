import type { CameraEvent, EntranceEvent, QueueEvent, TableEvent } from "@/types/events";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:4000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${path} responded with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fetchTableEvents(limit = 500): Promise<TableEvent[]> {
  return getJson<TableEvent[]>(`/events/tables?limit=${limit}`);
}

export function fetchCameraEvents(limit = 500): Promise<CameraEvent[]> {
  return getJson<CameraEvent[]>(`/events/cameras?limit=${limit}`);
}

export function fetchEntranceEvents(limit = 500): Promise<EntranceEvent[]> {
  return getJson<EntranceEvent[]>(`/events/entrance?limit=${limit}`);
}

export function fetchQueueEvents(limit = 500): Promise<QueueEvent[]> {
  return getJson<QueueEvent[]>(`/events/queue?limit=${limit}`);
}
