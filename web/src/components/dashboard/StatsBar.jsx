import { cn } from "../../lib/utils";

function StatCard({ n, label, hot, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-lg border bg-surface px-5 py-4 text-left transition-all duration-150",
        "hover:border-text-tertiary hover:shadow-sm",
        hot && n > 0 && "border-l-2 border-l-danger",
        active ? "border-accent ring-2 ring-accent-weak" : "border-border"
      )}
    >
      <div
        className={cn(
          "text-[clamp(26px,5vw,36px)] font-bold leading-none tracking-tight tabular-nums",
          hot && n > 0 ? "text-danger" : "text-text-primary"
        )}
      >
        {n}
      </div>
      <div className="mt-2 text-[11px] font-medium uppercase tracking-wider text-text-tertiary">
        {label}
      </div>
    </button>
  );
}

export function StatsBar({ stats, L, filter, setFilter }) {
  const counts = stats?.counts || {};
  const items = [
    { n: stats?.total ?? 0, label: L.stat.reviewed, hot: false, key: "all" },
    { n: counts.attention || 0, label: L.stat.attention, hot: true, key: "attention" },
    { n: counts.duplicates || 0, label: L.stat.duplicates, hot: false, key: "duplicates" },
    { n: counts.ready || 0, label: L.stat.ready, hot: false, key: "ready" },
    { n: counts.good_first || 0, label: L.stat.good_first, hot: false, key: "good_first" },
    { n: counts.more_info || 0, label: L.stat.more_info, hot: false, key: "more_info" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 py-7 sm:grid-cols-3 lg:grid-cols-6">
      {items.map((item) => (
        <StatCard
          key={item.key}
          {...item}
          active={filter === item.key}
          onClick={() => setFilter(filter === item.key ? "all" : item.key)}
        />
      ))}
    </div>
  );
}
