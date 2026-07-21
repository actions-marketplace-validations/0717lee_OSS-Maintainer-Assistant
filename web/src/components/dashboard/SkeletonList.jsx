export function SkeletonList() {
  return (
    <div className="space-y-0">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-3 border-b border-border px-3.5 py-4 first:border-t"
        >
          <div className="h-3.5 w-10 animate-pulse rounded bg-track" />
          <div className="h-4 w-7 animate-pulse rounded bg-track" />
          <div className="h-4 flex-1 animate-pulse rounded bg-track" style={{ maxWidth: `${55 - i * 5}%` }} />
          <div className="h-4 w-16 animate-pulse rounded bg-track" />
          <div className="h-4 w-20 animate-pulse rounded bg-track" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonStats() {
  return (
    <div className="grid grid-cols-2 gap-3 py-7 sm:grid-cols-3 lg:grid-cols-6">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="rounded-lg border border-border bg-surface px-5 py-4">
          <div className="h-8 w-12 animate-pulse rounded bg-track" />
          <div className="mt-2 h-3 w-16 animate-pulse rounded bg-track" />
        </div>
      ))}
    </div>
  );
}
