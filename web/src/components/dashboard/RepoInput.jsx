import { Search } from "lucide-react";

export function RepoInput({ repo, setRepo, onAnalyze, L }) {
  return (
    <div className="flex flex-wrap items-center gap-2.5">
      <div className="relative min-w-[280px] flex-1 sm:min-w-[300px]">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
        <input
          value={repo}
          placeholder={L.placeholder}
          onChange={(e) => setRepo(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") onAnalyze(repo.trim()); }}
          className="w-full rounded-lg border border-border-focus bg-surface py-2.5 pl-9 pr-3.5 text-sm text-text-primary placeholder:text-text-tertiary transition-all duration-150 focus:border-accent focus:outline-none focus:ring-[3px] focus:ring-accent-weak"
        />
      </div>
      <button
        onClick={() => onAnalyze(repo.trim())}
        className="rounded-lg border border-accent bg-accent px-4 py-2.5 text-sm font-semibold text-canvas transition-all duration-150 hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-weak"
      >
        {L.analyze}
      </button>
      <span className="text-xs text-text-tertiary">{L.hint}</span>
    </div>
  );
}
