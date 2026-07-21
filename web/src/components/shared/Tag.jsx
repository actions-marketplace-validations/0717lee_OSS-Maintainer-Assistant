import { cn } from "../../lib/utils";
import { tone, tV } from "../../lib/i18n";

const toneStyles = {
  danger: "bg-danger/10 text-danger border-danger/20",
  warning: "bg-warning/10 text-warning border-warning/20",
  success: "bg-success/10 text-success border-success/20",
  info: "bg-info/10 text-info border-info/20",
  neutral: "bg-neutral/10 text-text-secondary border-border",
};

const dotStyles = {
  danger: "bg-danger",
  warning: "bg-warning",
  success: "bg-success",
  info: "bg-info",
  neutral: "bg-neutral",
};

export function Tag({ text, lang, size = "sm" }) {
  const t = tone(text);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border font-medium whitespace-nowrap",
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-[13px]",
        toneStyles[t]
      )}
    >
      <i className={cn("h-1.5 w-1.5 rounded-full", dotStyles[t])} />
      {tV(lang, text)}
    </span>
  );
}
