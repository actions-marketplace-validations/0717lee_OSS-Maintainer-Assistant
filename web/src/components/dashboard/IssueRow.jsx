import { useState } from "react";
import { ChevronRight } from "lucide-react";
import { cn } from "../../lib/utils";
import { tone, tPri } from "../../lib/i18n";
import { Tag } from "../shared/Tag";
import { ConfidenceMeter } from "../shared/ConfidenceMeter";
import { AgentBlock } from "./AgentBlock";
import { ApproveBar } from "./ApproveBar";
import { AskBar } from "./AskBar";
import { ContributorProfile } from "./ContributorProfile";
import { CIAnalyzer } from "./CIAnalyzer";

const decisionOf = (r, name) => (r.results.find((x) => x.agent === name) || {}).decision;
const actionOf = (r, type) => r.actions.find((a) => a.type === type);

export function IssueRow({ r, lang, L, repo }) {
  const [open, setOpen] = useState(false);
  const it = r.item;
  const tri = decisionOf(r, "triage") || {};
  const qual = decisionOf(r, "quality") || {};
  const slop = qual.data?.slop_score || 0;
  const labels = actionOf(r, "add_labels")?.payload.labels || [];
  const pri = tri.data?.priority || "-";
  const kindLabel = it.kind === "pull_request" ? "PR" : "issue";
  const applicable = qual.verdict && qual.verdict !== "not-applicable";
  const shown = ["triage", "quality", "reproducer", "responder"]
    .map((a) => [a, decisionOf(r, a)])
    .filter(([, d]) => d);

  return (
    <div className="border-b border-border first:border-t">
      {/* Row header */}
      <div
        onClick={() => setOpen(!open)}
        className={cn(
          "relative flex cursor-pointer flex-wrap items-center gap-x-3 gap-y-2 rounded-lg px-3.5 py-4 transition-all duration-150",
          "hover:bg-surface hover:shadow-[inset_2px_0_0_var(--accent)]",
          open && "bg-surface shadow-[inset_2px_0_0_var(--accent)]"
        )}
      >
        <span className="min-w-[50px] font-mono text-xs text-text-tertiary">#{it.number}</span>
        <span className="hidden rounded border border-border-focus px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-text-tertiary sm:inline-block">
          {kindLabel}
        </span>
        <span className="min-w-0 flex-1 truncate text-[15px] font-semibold tracking-tight text-text-primary max-sm:basis-full max-sm:order-3">
          {it.title}
        </span>
        <span className="flex flex-shrink-0 flex-wrap items-center gap-x-3.5 gap-y-1.5 max-sm:basis-full max-sm:order-4">
          <span
            className={cn(
              "font-mono text-[11.5px] uppercase tracking-wide text-text-tertiary",
              pri === "high" && "text-danger",
              pri === "medium" && "text-warning"
            )}
          >
            {tPri(lang, pri)}
          </span>
          <Tag text={tri.verdict || "-"} lang={lang} />
          {applicable && (
            <>
              <Tag text={qual.verdict} lang={lang} />
              <ConfidenceMeter verdict={qual.verdict} score={slop} />
            </>
          )}
        </span>
        <ChevronRight
          size={16}
          className={cn(
            "absolute right-2.5 top-4 text-text-tertiary transition-transform duration-200 sm:static sm:self-center",
            open && "rotate-90 text-accent"
          )}
        />
      </div>

      {/* Expandable body */}
      <div
        className={cn(
          "grid transition-all duration-250 ease-[cubic-bezier(0.16,1,0.3,1)]",
          open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
        )}
      >
        <div className="overflow-hidden">
          <div className="px-4 pb-6 pt-1">
            {labels.length > 0 && (
              <div className="mb-2 flex flex-wrap gap-2">
                {labels.map((l) => (
                  <Tag key={l} text={l} lang={lang} />
                ))}
              </div>
            )}
            <ContributorProfile author={it.author} repo={repo} lang={lang} />
            {shown.map(([a, d]) => (
              <AgentBlock key={a} name={a} decision={d} lang={lang} L={L} />
            ))}
            <ApproveBar
              actions={r.actions.filter((a) => a.type !== "none")}
              repo={repo}
              itemNumber={it.number}
              itemTitle={it.title}
              lang={lang}
              L={L}
            />
            <AskBar repo={repo} itemNumber={it.number} lang={lang} />
            {it.kind === "pull_request" && <CIAnalyzer repo={repo} lang={lang} />}
          </div>
        </div>
      </div>
    </div>
  );
}
