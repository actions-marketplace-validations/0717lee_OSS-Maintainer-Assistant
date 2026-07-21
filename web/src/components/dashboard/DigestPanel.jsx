import { FileText } from "lucide-react";

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

export function DigestPanel({ digestMd, L }) {
  return (
    <aside className="lg:sticky lg:top-24 lg:h-[calc(100vh-7rem)]">
      <div className="flex h-full flex-col rounded-xl border border-border bg-elevated p-5 shadow-elevate">
        <div className="mb-4 flex items-center gap-2">
          <FileText size={14} className="text-text-tertiary" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-text-tertiary">
            {L.digestTitle}
          </h2>
        </div>
        <div
          className="digest-md flex-1 overflow-y-auto text-[13px] leading-relaxed text-text-secondary"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(digestMd) }}
        />
      </div>
    </aside>
  );
}
