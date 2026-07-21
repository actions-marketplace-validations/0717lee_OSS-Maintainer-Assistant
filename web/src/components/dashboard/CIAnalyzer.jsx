import { useState } from "react";
import { Terminal, Loader2, ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "../../lib/utils";

const SEVERITY_STYLES = {
  danger: "text-danger bg-danger/10 border-danger/30",
  warning: "text-warning bg-warning/10 border-warning/30",
  info: "text-info bg-info/10 border-info/30",
  neutral: "text-text-tertiary bg-surface border-border",
};

export function CIAnalyzer({ repo, lang }) {
  const [logText, setLogText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showLog, setShowLog] = useState(false);

  async function analyze() {
    if (!logText.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch("/api/ci-analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo, log_text: logText.trim() }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResult(await res.json());
    } catch (e) {
      setResult({ error: String(e) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-5 rounded-lg border border-border bg-surface/50 p-4">
      <div className="mb-3 flex items-center gap-2">
        <Terminal size={14} className="text-text-tertiary" />
        <span className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
          {lang === "zh" ? "CI 失败分析" : "CI Failure Analysis"}
        </span>
      </div>

      <textarea
        value={logText}
        onChange={(e) => setLogText(e.target.value)}
        placeholder={lang === "zh" ? "粘贴 CI 日志文本…" : "Paste CI log text here…"}
        rows={4}
        className="w-full rounded-lg border border-border-focus bg-surface px-3 py-2 font-mono text-xs text-text-primary placeholder:text-text-tertiary focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent-weak"
      />

      <button
        onClick={analyze}
        disabled={loading || !logText.trim()}
        className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-accent bg-accent px-3 py-1.5 text-xs font-semibold text-canvas transition-all duration-150 hover:opacity-90 disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-weak"
      >
        {loading ? <Loader2 size={13} className="animate-spin" /> : <Terminal size={13} />}
        {lang === "zh" ? "分析" : "Analyze"}
      </button>

      {result && !result.error && (
        <div className="mt-3 space-y-3">
          <div className="flex items-center gap-2">
            <span className={cn("inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium", SEVERITY_STYLES[result.severity] || SEVERITY_STYLES.neutral)}>
              {result.label}
            </span>
            <span className="text-xs text-text-tertiary">{result.summary}</span>
          </div>

          {result.diagnosis && (
            <div className="rounded-lg border border-border border-l-2 border-l-info bg-elevated p-3 text-sm text-text-secondary">
              <p className="whitespace-pre-wrap">{result.diagnosis}</p>
            </div>
          )}

          {result.matched?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {result.matched.map((m, i) => (
                <span key={i} className="rounded-md border border-border bg-surface px-2 py-0.5 text-xs text-text-secondary">
                  {m.description} ({m.count})
                </span>
              ))}
            </div>
          )}

          {result.error_lines?.length > 0 && (
            <div>
              <button
                onClick={() => setShowLog(!showLog)}
                className="flex items-center gap-1 text-xs text-text-tertiary hover:text-text-secondary"
              >
                {showLog ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                {lang === "zh" ? "错误行" : "Error lines"}
              </button>
              {showLog && (
                <pre className="mt-2 max-h-40 overflow-auto rounded-lg border border-border bg-base p-2.5 text-xs text-text-secondary">
                  {result.error_lines.join("\n")}
                </pre>
              )}
            </div>
          )}
        </div>
      )}

      {result?.error && <p className="mt-2 text-xs text-danger">{result.error}</p>}
    </div>
  );
}
