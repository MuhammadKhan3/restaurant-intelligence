import { tableStateStyle } from "@/lib/status";
import type { TableStatus } from "@/types/events";

import { OccupancyTimer } from "@/components/dashboard/OccupancyTimer";

export function TableStatusCard({ table }: { table: TableStatus }) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          {table.zoneId}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${tableStateStyle(table.state)}`}
        >
          {table.state}
        </span>
      </div>
      {table.state === "occupied" && <OccupancyTimer since={table.since} />}
    </div>
  );
}
