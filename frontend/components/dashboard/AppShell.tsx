import type { ReactNode } from "react";

import { Navigation } from "@/components/dashboard/Navigation";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
        <span className="text-sm font-semibold uppercase tracking-widest text-zinc-500 dark:text-zinc-400">
          Restaurant Intelligence
        </span>
        <Navigation />
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
