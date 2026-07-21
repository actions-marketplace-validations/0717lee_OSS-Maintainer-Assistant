import { Tag } from "../shared/Tag";
import { tAgent } from "../../lib/i18n";

export function AgentBlock({ decision, name, lang, L }) {
  if (!decision) return null;

  return (
    <div className="border-t border-border py-3.5 first:border-t-0">
      <div className="flex items-center gap-2.5">
        <span className="text-[10.5px] font-semibold uppercase tracking-wider text-text-tertiary">
          {tAgent(lang, name)}
        </span>
        <Tag text={decision.verdict} lang={lang} />
        <span className="ml-auto font-mono text-[11px] text-text-tertiary">
          {L.conf} {(decision.confidence || 0).toFixed(2)}
        </span>
      </div>

      <p className="mt-1.5 text-[13.5px] text-text-secondary">{decision.rationale}</p>

      {(decision.evidence || []).map((e, i) => (
        <div key={i} className="relative mt-1 pl-4 text-xs text-text-secondary">
          <i className="absolute left-0.5 top-[7px] h-[5px] w-[5px] rounded-full bg-border-focus" />
          <span className="text-text-tertiary">{e.kind}</span> · {e.detail}
          {e.weight ? (
            <span className={`font-mono ${e.weight > 0 ? "text-danger" : "text-success"}`}>
              {" "}{e.weight > 0 ? "+" : ""}{e.weight.toFixed(2)}
            </span>
          ) : null}
        </div>
      ))}

      {name === "responder" && decision.data?.draft ? (
        <>
          <div className="mt-4 text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">
            {L.draft}
          </div>
          <div className="mt-1.5 whitespace-pre-wrap rounded-lg border border-border border-l-2 border-l-accent bg-surface p-3.5 text-[13.5px] text-text-primary">
            {decision.data.draft}
          </div>
        </>
      ) : null}
    </div>
  );
}
