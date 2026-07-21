import { Loader2, FileText } from "lucide-react";
import { IssueRow } from "./IssueRow";
import { SkeletonList } from "./SkeletonList";
import { EmptyState } from "./EmptyState";

function matchesFilter(r, filter) {
  if (filter === "all") return true;
  const tri = (r.results.find((x) => x.agent === "triage") || {}).decision || {};
  const qual = (r.results.find((x) => x.agent === "quality") || {}).decision || {};
  const td = tri.data || {};
  switch (filter) {
    case "attention":
      return qual.verdict === "likely-ai-slop" || tri.verdict === "security";
    case "duplicates":
      return !!td.duplicate_of;
    case "ready":
      return r.item.is_pr && qual.verdict === "looks-good";
    case "good_first":
      return !!td.good_first_issue;
    case "more_info":
      return !!td.needs_more_info;
    default:
      return true;
  }
}

export function IssueList({ data, error, loading, repo, lang, L, onRetry, onOpenDigest, filter = "all" }) {
  return (
    <section>
      <div className="mb-1.5 flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-text-tertiary">
          {L.listTitle}
        </span>
        {data && onOpenDigest && (
          <button
            onClick={onOpenDigest}
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-xs font-medium text-text-secondary transition-all duration-150 hover:bg-surface hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-weak"
          >
            <FileText size={13} />
            {L.digestTitle}
          </button>
        )}
      </div>
      <div className="mt-1">
        {loading && (
          <>
            <div className="flex items-center gap-2 px-1 py-3 text-sm text-text-secondary">
              <Loader2 size={16} className="animate-spin text-text-tertiary" />
              <span>
                {lang === "zh"
                  ? `正在分析 ${repo || "仓库"}，多 Agent 并行处理中，预计 30-60 秒…`
                  : `Analyzing ${repo || "repository"} — multi-agent pipeline running, ~30-60s…`}
              </span>
            </div>
            <SkeletonList />
          </>
        )}
        {error && !loading && (
          <EmptyState
            variant="error"
            message={`${L.errPre}${error}${L.errSuf}`}
            onRetry={onRetry}
            retryLabel={L.retry}
          />
        )}
        {!data && !error && !loading && (
          <EmptyState
            variant="empty"
            message={L.emptyHint}
            title={L.empty}
          />
        )}
        {data && !loading && (() => {
          const filtered = data.results.filter((r) => matchesFilter(r, filter));
          if (filtered.length === 0) {
            return (
              <EmptyState
                variant="empty"
                message={lang === "zh" ? "没有符合该筛选的条目。" : "No items match this filter."}
                title={lang === "zh" ? "空" : "Empty"}
              />
            );
          }
          return filtered.map((r) => (
            <IssueRow key={r.item.number} r={r} lang={lang} L={L} repo={data.repo} />
          ));
        })()}
      </div>
    </section>
  );
}
