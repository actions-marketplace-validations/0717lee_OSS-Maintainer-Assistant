import { cn } from "../../lib/utils";
import { tone } from "../../lib/i18n";

const barStyles = {
  danger: "bg-danger",
  warning: "bg-warning",
  success: "bg-success",
  info: "bg-info",
  neutral: "bg-neutral",
};

export function ConfidenceMeter({ verdict, score }) {
  const t = tone(verdict);
  const pct = Math.round((score || 0) * 100);

  return (
    <span className="inline-flex items-center gap-2">
      <span className="inline-block h-[5px] w-11 overflow-hidden rounded-full bg-track">
        <i
          className={cn("block h-full rounded-full transition-all duration-500", barStyles[t])}
          style={{ width: pct + "%" }}
        />
      </span>
      <span className="font-mono text-xs text-text-tertiary tabular-nums">{score}</span>
    </span>
  );
}
