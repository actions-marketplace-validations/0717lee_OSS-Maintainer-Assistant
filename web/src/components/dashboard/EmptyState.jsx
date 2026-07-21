import { Inbox, AlertTriangle } from "lucide-react";

export function EmptyState({ variant = "empty", title, message, onRetry, retryLabel }) {
  const isError = variant === "error";

  return (
    <div
      className={`flex flex-col items-center justify-center rounded-lg border px-6 py-14 text-center ${
        isError ? "border-danger/30 bg-danger/5" : "border-border bg-surface"
      }`}
    >
      {isError ? (
        <AlertTriangle size={28} className="mb-3 text-danger" />
      ) : (
        <Inbox size={28} className="mb-3 text-text-tertiary" />
      )}
      {title && (
        <div className="mb-1 text-sm font-semibold text-text-primary">{title}</div>
      )}
      <p className="max-w-sm text-[13px] text-text-secondary">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 rounded-lg border border-border-focus px-4 py-2 text-sm font-medium text-text-primary transition-all duration-150 hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-weak"
        >
          {retryLabel || "Retry"}
        </button>
      )}
    </div>
  );
}
