import { cameraStatusStyle } from "@/lib/status";
import type { CameraStatus } from "@/types/events";

export function CameraStatusList({ cameras }: { cameras: CameraStatus[] }) {
  if (cameras.length === 0) {
    return <p className="text-sm text-zinc-500 dark:text-zinc-400">No cameras reporting yet.</p>;
  }

  return (
    <ul className="flex flex-wrap gap-2">
      {cameras.map((camera) => (
        <li
          key={camera.cameraId}
          className={`rounded-full px-3 py-1 text-xs font-medium capitalize ${cameraStatusStyle(camera.status)}`}
        >
          {camera.cameraId}: {camera.status}
        </li>
      ))}
    </ul>
  );
}
