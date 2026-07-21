import { useState, useEffect } from "react";
import { User, AlertTriangle, ShieldCheck, HelpCircle, Loader2 } from "lucide-react";
import { cn } from "../../lib/utils";

const RISK_STYLES = {
  high: { icon: AlertTriangle, color: "text-danger", bg: "bg-danger/10", border: "border-danger/30",
    label_en: "High risk", label_zh: "高风险" },
  medium: { icon: AlertTriangle, color: "text-warning", bg: "bg-warning/10", border: "border-warning/30",
    label_en: "Medium risk", label_zh: "中风险" },
  low: { icon: ShieldCheck, color: "text-success", bg: "bg-success/10", border: "border-success/30",
    label_en: "Low risk", label_zh: "低风险" },
  unknown: { icon: HelpCircle, color: "text-text-tertiary", bg: "bg-surface", border: "border-border",
    label_en: "No history", label_zh: "无历史记录" },
};

export function ContributorProfile({ author, repo, lang }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!author || !repo) { setLoading(false); return; }
    setLoading(true);
    fetch(`/api/memory/${encodeURIComponent(repo)}/contributors/${encodeURIComponent(author)}`)
      .then((r) => r.ok ? r.json() : null)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [author, repo]);

  if (loading) {
    return (
      <div className="mt-4 flex items-center gap-2 rounded-lg border border-border bg-surface/50 px-3 py-2 text-xs text-text-tertiary">
        <Loader2 size={13} className="animate-spin" />
        {lang === "zh" ? "加载贡献者画像…" : "Loading contributor profile…"}
      </div>
    );
  }

  if (!data || !data.stats || !data.stats.total_prs && !data.stats.total_issues) {
    return null; // Don't show anything for first-time contributors.
  }

  const risk = data.risk || "unknown";
  const rs = RISK_STYLES[risk];
  const Icon = rs.icon;
  const s = data.stats;
  const total = (s.total_prs || 0) + (s.total_issues || 0);
  const slopRate = total > 0 ? ((s.slop_count || 0) / total * 100).toFixed(0) : 0;

  return (
    <div className="mt-4 rounded-lg border border-border bg-surface/50 p-3">
      <div className="flex items-center gap-2">
        <User size={14} className="text-text-tertiary" />
        <span className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
          {lang === "zh" ? "贡献者画像" : "Contributor Profile"}
        </span>
        <span className={cn("ml-auto inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium", rs.border, rs.bg, rs.color)}>
          <Icon size={12} />
          {lang === "zh" ? rs.label_zh : rs.label_en}
        </span>
      </div>
      <div className="mt-2.5 flex flex-wrap gap-x-5 gap-y-1.5 text-xs text-text-secondary">
        <span>{lang === "zh" ? "PR" : "PRs"}: <b className="text-text-primary">{s.total_prs || 0}</b></span>
        <span>{lang === "zh" ? "Issue" : "Issues"}: <b className="text-text-primary">{s.total_issues || 0}</b></span>
        <span>{lang === "zh" ? "灌水" : "Slop"}: <b className="text-danger">{s.slop_count || 0}</b> ({slopRate}%)</span>
        {s.avg_slop_score > 0 && (
          <span>{lang === "zh" ? "平均分" : "Avg score"}: <b className="text-text-primary">{(s.avg_slop_score || 0).toFixed(2)}</b></span>
        )}
        <span className="text-text-tertiary">@{s.last_seen?.slice(0, 10)}</span>
      </div>
    </div>
  );
}
