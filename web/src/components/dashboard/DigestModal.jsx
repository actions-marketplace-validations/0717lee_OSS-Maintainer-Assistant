import { FileText, X } from "lucide-react";

function renderMarkdown(md) {
  const lines = (md || "").split("\n");
  let html = "", inList = false;
  const esc = (s) => (s || "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  const inline = (t) =>
    esc(t)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\[(.+?)\]\((.+?)\)/g, (m, t2, u) =>
        /^https?:\/\/[^"\s]+$/i.test(u) ? `<a href="${u}" target="_blank" rel="noopener">${t2}</a>` : m)
      .replace(/_(.+?)_/g, "<em>$1</em>");
  for (const line of lines) {
    if (line.startsWith("## ")) { if (inList) { html += "</ul>"; inList = false; } html += "<h4>" + inline(line.slice(3)) + "</h4>"; }
    else if (line.startsWith("# ")) { if (inList) { html += "</ul>"; inList = false; } html += "<h3>" + inline(line.slice(2)) + "</h3>"; }
    else if (line.startsWith("> ")) { html += "<blockquote>" + inline(line.slice(2)) + "</blockquote>"; }
    else if (line.startsWith("- ")) { if (!inList) { html += "<ul>"; inList = true; } html += "<li>" + inline(line.slice(2)) + "</li>"; }
    else { if (inList) { html += "</ul>"; inList = false; } if (line.trim()) html += "<p>" + inline(line) + "</p>"; }
  }
  if (inList) html += "</ul>";
  return html;
}

export function DigestModal({ open, digestMd, L, onClose }) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="relative mx-4 my-8 flex max-h-[85vh] w-full max-w-2xl flex-col rounded-xl border border-border bg-elevated shadow-elevate"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-2 border-b border-border px-5 py-4">
          <FileText size={16} className="text-text-tertiary" />
          <h2 className="flex-1 text-sm font-bold uppercase tracking-wider text-text-tertiary">
            {L.digestTitle}
          </h2>
          <button
            onClick={onClose}
            className="text-text-tertiary transition-colors hover:text-text-primary"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="digest-md overflow-y-auto px-5 py-4 text-[13px] leading-relaxed text-text-secondary">
          <div dangerouslySetInnerHTML={{ __html: renderMarkdown(digestMd) }} />
        </div>
      </div>
    </div>
  );
}
