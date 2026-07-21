import { useState } from "react";
import { Check, X, Loader2, Tag, MessageSquare, XCircle, RotateCcw } from "lucide-react";
import { cn } from "../../lib/utils";
import { ConfirmDialog } from "../shared/ConfirmDialog";

const ACTION_ICONS = {
  add_labels: Tag,
  comment: MessageSquare,
  close: XCircle,
};

const ACTION_LABELS = {
  en: { add_labels: "Add labels", comment: "Post comment", close: "Close issue" },
  zh: { add_labels: "添加标签", comment: "发布评论", close: "关闭 Issue" },
};

export function ApproveBar({ actions, repo, itemNumber, itemTitle, lang, L }) {
  const [dialogAction, setDialogAction] = useState(null);
  const [statusMap, setStatusMap] = useState({});

  const labels = ACTION_LABELS[lang] || ACTION_LABELS.en;

  async function doApprove(action) {
    const key = action.type;
    setStatusMap((prev) => ({ ...prev, [key]: "loading" }));
    setDialogAction(null);
    try {
      const res = await fetch("/api/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo,
          item_number: itemNumber,
          item_title: itemTitle,
          action_type: action.type,
          payload: action.payload,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = err.detail || "";
        // Humanize common errors.
        let friendly;
        if (res.status === 403 || "GITHUB_TOKEN" in detail) {
          friendly = lang === "zh"
            ? "GitHub Token 未配置，无法发布。请在 .env 中设置 GITHUB_TOKEN。"
            : "GitHub Token not configured. Set GITHUB_TOKEN in .env to enable publishing.";
        } else if (res.status === 404) {
          friendly = lang === "zh"
            ? "Issue 或 PR 不存在，或 Token 缺少该仓库的写权限。"
            : "Issue/PR not found, or the token lacks write access to this repo.";
        } else if (res.status === 401) {
          friendly = lang === "zh"
            ? "Token 无效或已过期，请重新生成。"
            : "Token is invalid or expired. Please regenerate it.";
        } else if (res.status === 502) {
          friendly = lang === "zh"
            ? "GitHub API 返回错误，可能是限流或网络问题，请稍后重试。"
            : "GitHub API error — possibly rate-limited or a network issue. Try again later.";
        } else {
          friendly = lang === "zh"
            ? `操作失败（${res.status}）：${detail}`
            : `Operation failed (${res.status}): ${detail}`;
        }
        throw new Error(friendly);
      }
      setStatusMap((prev) => ({ ...prev, [key]: "applied" }));
    } catch (e) {
      setStatusMap((prev) => ({ ...prev, [key]: "error", [key + "_err"]: String(e).replace(/^Error:\s*/, "") }));
    }
  }

  if (!actions.length) return null;

  return (
    <div className="mt-5 rounded-lg border border-border bg-surface/50 p-4">
      <div className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
        {L.proposed}
      </div>
      <div className="space-y-2">
        {actions.map((action) => {
          const Icon = ACTION_ICONS[action.type] || Check;
          const status = statusMap[action.type] || "pending";

          return (
            <div
              key={action.type}
              className="flex items-center gap-3 rounded-lg border border-border bg-elevated px-3 py-2.5"
            >
              <Icon size={15} className="flex-shrink-0 text-text-tertiary" />
              <div className="min-w-0 flex-1">
                <span className="text-sm font-medium text-text-primary">
                  {labels[action.type] || action.type}
                </span>
                {action.payload?.labels && (
                  <span className="ml-2 text-xs text-text-tertiary">
                    {action.payload.labels.join(", ")}
                  </span>
                )}
                {action.payload?.body && (
                  <p className="mt-1 truncate text-xs text-text-tertiary">
                    {action.payload.body.slice(0, 80)}…
                  </p>
                )}
                {status === "error" && (
                  <div className="mt-1.5 rounded-md border border-danger/20 bg-danger/5 px-2.5 py-1.5 text-xs text-danger">
                    {statusMap[action.type + "_err"]}
                  </div>
                )}
              </div>
              <div className="flex-shrink-0">
                {status === "loading" ? (
                  <Loader2 size={16} className="animate-spin text-text-tertiary" />
                ) : status === "applied" ? (
                  <span className="inline-flex items-center gap-1.5 rounded-md bg-success/10 px-2 py-1 text-xs font-medium text-success">
                    <Check size={13} /> {lang === "zh" ? "已执行" : "Applied"}
                  </span>
                ) : status === "error" ? (
                  <button
                    onClick={() => setDialogAction(action)}
                    className="inline-flex items-center gap-1 rounded-md border border-border-focus bg-transparent px-2.5 py-1 text-xs font-medium text-text-secondary transition-all duration-150 hover:bg-surface hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-weak"
                  >
                    <RotateCcw size={12} />
                    {lang === "zh" ? "重试" : "Retry"}
                  </button>
                ) : (
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => setDialogAction(action)}
                      disabled={status === "applied"}
                      className="inline-flex items-center gap-1 rounded-md border border-accent bg-accent px-2.5 py-1 text-xs font-semibold text-canvas transition-all duration-150 hover:opacity-90 disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-weak"
                    >
                      <Check size={12} />
                      {lang === "zh" ? "批准" : "Approve"}
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <ConfirmDialog
        open={!!dialogAction}
        variant="danger"
        title={
          lang === "zh" ? "确认执行此操作？" : "Confirm this action?"
        }
        message={
          lang === "zh"
            ? `将在 ${repo} #${itemNumber} 上执行「${labels[dialogAction?.type] || ""}」。此操作不可撤销。`
            : `This will ${labels[dialogAction?.type] || dialogAction?.type} on ${repo} #${itemNumber}. This action cannot be undone.`
        }
        confirmLabel={lang === "zh" ? "确认发布" : "Confirm & Publish"}
        cancelLabel={lang === "zh" ? "取消" : "Cancel"}
        onConfirm={() => doApprove(dialogAction)}
        onCancel={() => setDialogAction(null)}
      />
    </div>
  );
}
