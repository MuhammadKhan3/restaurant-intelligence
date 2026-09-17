"use client";

import { useEffect, useState } from "react";

import {
  fetchCameraEvents,
  fetchEntranceEvents,
  fetchQueueEvents,
  fetchTableEvents,
} from "@/lib/api";
import {
  deriveCameraStatuses,
  deriveCustomerCount,
  deriveTableStatuses,
  deriveWaitingCount,
} from "@/lib/status";
import type { CameraStatus, TableStatus } from "@/types/events";

import { CameraStatusList } from "@/components/dashboard/CameraStatusList";
import { CustomerCount } from "@/components/dashboard/CustomerCount";
import { TableStatusCard } from "@/components/dashboard/TableStatusCard";

const POLL_INTERVAL_MS = 5000;

export function FloorView() {
  const [tables, setTables] = useState<TableStatus[]>([]);
  const [cameras, setCameras] = useState<CameraStatus[]>([]);
  const [customerCount, setCustomerCount] = useState(0);
  const [waitingCount, setWaitingCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const [tableEvents, cameraEvents, entranceEvents, queueEvents] = await Promise.all([
          fetchTableEvents(),
          fetchCameraEvents(),
          fetchEntranceEvents(),
          fetchQueueEvents(),
        ]);
        if (cancelled) return;
        setTables(deriveTableStatuses(tableEvents));
        setCameras(deriveCameraStatuses(cameraEvents));
        setCustomerCount(deriveCustomerCount(entranceEvents));
        setWaitingCount(deriveWaitingCount(queueEvents));
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load live data");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex flex-col gap-8 px-6 py-8">
      <section className="flex flex-wrap gap-8">
        <CustomerCount count={customerCount} />
        <CustomerCount count={waitingCount} label="customers waiting in queue" />
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium uppercase tracking-widest text-zinc-500 dark:text-zinc-400">
          Cameras
        </h2>
        <CameraStatusList cameras={cameras} />
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium uppercase tracking-widest text-zinc-500 dark:text-zinc-400">
          Floor
        </h2>

        {error && (
          <p className="text-sm text-red-600 dark:text-red-400">
            Couldn&apos;t reach the backend: {error}
          </p>
        )}

        {!error && loading && (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading table status…</p>
        )}

        {!error && !loading && tables.length === 0 && (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            No table events yet. Table state changes reported by cv-service will appear here.
          </p>
        )}

        {tables.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {tables.map((table) => (
              <TableStatusCard key={table.zoneId} table={table} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
