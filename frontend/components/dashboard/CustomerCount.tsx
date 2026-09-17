export function CustomerCount({ count }: { count: number }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-3xl font-semibold tabular-nums text-zinc-900 dark:text-zinc-50">
        {count}
      </span>
      <span className="text-sm text-zinc-500 dark:text-zinc-400">customers currently inside</span>
    </div>
  );
}
