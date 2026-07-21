import { useState } from "react";
import { Send, Loader2, MessageCircle } from "lucide-react";

export function AskBar({ repo, itemNumber, lang }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function ask() {
    if (!question.trim()) return;
    setLoading(true);
    setError("");
    setAnswer("");
    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo, item_number: itemNumber, question: question.trim() }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setAnswer(data.answer);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-5 rounded-lg border border-border bg-surface/50 p-4">
      <div className="mb-3 flex items-center gap-2">
        <MessageCircle size={14} className="text-text-tertiary" />
        <span className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
          {lang === "zh" ? "追问 Agent" : "Ask Agent"}
        </span>
      </div>
      <div className="flex gap-2">
        <input
          value={question}
          placeholder={lang === "zh" ? "提问，例如：为什么判定为 AI 灌水？" : "Ask, e.g. why is this flagged as AI slop?"}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !loading) ask(); }}
          className="flex-1 rounded-lg border border-border-focus bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent-weak"
        />
        <button
          onClick={ask}
          disabled={loading || !question.trim()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-accent bg-accent px-3 py-2 text-sm font-semibold text-canvas transition-all duration-150 hover:opacity-90 disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-weak"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          {lang === "zh" ? "提问" : "Ask"}
        </button>
      </div>
      {error && <p className="mt-2 text-xs text-danger">{error}</p>}
      {answer && (
        <div className="mt-3 rounded-lg border border-border border-l-2 border-l-info bg-elevated p-3 text-sm text-text-secondary">
          <p className="whitespace-pre-wrap">{answer}</p>
        </div>
      )}
    </div>
  );
}
