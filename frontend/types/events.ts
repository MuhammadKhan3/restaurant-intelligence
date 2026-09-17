export type TableEvent = {
  id: number;
  zone_id: string;
  from_state: string;
  to_state: string;
  occurred_at: string;
  received_at: string;
};

export type CameraEvent = {
  id: number;
  camera_id: string;
  status: string;
  occurred_at: string;
  received_at: string;
};

export type TableStatus = {
  zoneId: string;
  state: string;
  since: string;
};

export type CameraStatus = {
  cameraId: string;
  status: string;
  since: string;
};

export type EntranceEvent = {
  id: number;
  zone_id: string;
  track_id: number;
  event_type: "entry" | "exit";
  occurred_at: string;
  received_at: string;
};

export type QueueEvent = {
  id: number;
  zone_id: string;
  track_id: number;
  event_type: "entry" | "exit";
  occurred_at: string;
  received_at: string;
};
