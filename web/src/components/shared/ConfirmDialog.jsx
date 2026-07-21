import { useState } from "react";
import { AlertTriangle, X } from "lucide-react";
import { cn } from "../../lib/utils";

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "default",
  onConfirm,
  onCancel,
}) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm animate-fade-in"
      onClick={onCancel}
    >
      <div
        className="relative mx-4 w-full max-w-md rounded-xl border border-border bg-elevated p-6 shadow-elevate"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onCancel}
          className="absolute right-4 top-4 text-text-tertiary hover:text-text-primary"
        >
          <X size={18} />
        </button>
        <div className="flex items-start gap-3">
          {variant === "danger" && (
            <AlertTriangle size={20} className="mt-0.5 flex-shrink-0 text-danger" />
          )}
          <div>
            <h3 className="text-base font-semibold text-text-primary">{title}</h3>
            <p className="mt-2 text-sm text-text-secondary">{message}</p>
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="rounded-lg border border-border-focus px-4 py-2 text-sm font-medium text-text-primary transition-all duration-150 hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-weak"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={cn(
              "rounded-lg border px-4 py-2 text-sm font-semibold transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-weak",
              variant === "danger"
                ? "border-danger bg-danger text-white hover:opacity-90"
                : "border-accent bg-accent text-canvas hover:opacity-90"
            )}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
