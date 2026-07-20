import React, { useEffect, useState } from "react";

const I18N = {
  en: {
    tagline: "A read-only, human-gated assistant that triages issues, flags likely AI slop, reproduces bugs, and drafts replies — every call shows its evidence.",
    placeholder: "owner/name  (leave blank for the offline demo)",
    analyze: "Analyze", demo: "Offline demo",
    hint: "Public repos work without a token (rate-limited).",
    listTitle: "Issues & pull requests", digestTitle: "Maintainer digest",
    footer: "Read-only by default · nothing is posted without approval · ", source: "source",
    loading: "Running the multi-agent pipeline…", loadingDemo: "Loading the offline demo…",
    conf: "conf", draft: "Suggested reply (draft)", proposed: "proposed actions (require approval): ",
    st: { source: "source", backend: "backend", llm: "llm", run: "run", items: "items" },
    stat: { reviewed: "reviewed", attention: "needs attention", duplicates: "duplicates",
      ready: "ready to review", good_first: "good first issue", more_info: "needs info" },
    errPre: "Couldn't load: ", errSuf: ". Check the owner/name and rate limits, or try the offline demo.",
  },
  zh: {
    tagline: "只读、需人工确认的助手：分诊 issue、识别疑似 AI 灌水、复现 bug、起草回复——每个判断都附证据。",
    placeholder: "owner/name（留空则加载离线演示）",
    analyze: "分析", demo: "离线演示",
    hint: "公开仓库无需 token 即可分析（有速率限制）。",
    listTitle: "Issues 与 Pull Requests", digestTitle: "维护者摘要",
    footer: "默认只读 · 未经批准不会发布 · ", source: "源码",
    loading: "正在运行多 Agent 流水线…", loadingDemo: "正在加载离线演示…",
    conf: "置信", draft: "建议回复（草稿）", proposed: "建议动作（需批准）：",
    st: { source: "来源", backend: "后端", llm: "模型", run: "运行", items: "条" },
    stat: { reviewed: "已审阅", attention: "需关注", duplicates: "疑似重复",
      ready: "待评审", good_first: "适合新手", more_info: "信息不足" },
    errPre: "加载失败：", errSuf: "。请检查 owner/name 与速率限制，或试用离线演示。",
  },
};
const VMAP_ZH = {
  "likely-ai-slop": "疑似 AI 灌水", "needs-work": "待完善", "looks-good": "良好", duplicate: "重复",
  security: "安全", bug: "缺陷", "needs-more-info": "信息不足", documentation: "文档",
  enhancement: "增强", question: "提问", reproduced: "已复现", "not-reproduced": "未复现",
  "reply-drafted": "已拟回复", "not-applicable": "不适用", "needs-triage": "待分诊", "good first issue": "适合新手",
};
const PRI_ZH = { high: "高", medium: "中", low: "低", "-": "-" };
const AGENT_ZH = { triage: "分诊", quality: "质量", reproducer: "复现", responder: "回复" };
const TONE = {
  "likely-ai-slop": "danger", security: "danger", bug: "danger", reproduced: "danger",
  "needs-work": "warning", "needs-more-info": "warning",
  "looks-good": "success", "not-reproduced": "success", "good first issue": "success",
  duplicate: "info", documentation: "info", enhancement: "info", question: "info",
  "reply-drafted": "neutral", "not-applicable": "neutral", "needs-triage": "neutral",
};
const tone = (v) => TONE[v] || "neutral";
const tV = (lang, v) => (lang === "zh" ? VMAP_ZH[v] || v : v);
const tPri = (lang, p) => (lang === "zh" ? PRI_ZH[p] || p : p);
const tAgent = (lang, a) => (lang === "zh" ? AGENT_ZH[a] || a : a);
const esc = (s) => (s || "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
const decisionOf = (r, name) => (r.results.find((x) => x.agent === name) || {}).decision;
const actionOf = (r, type) => r.actions.find((a) => a.type === type);

function renderMarkdown(md) {
  const lines = (md || "").split("\n");
  let html = "", inList = false;
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

const SunIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <circle cx="12" cy="12" r="4.2" />
    <path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4l1.4-1.4M18 6l1.4-1.4" />
  </svg>
);
const MoonIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round">
    <path d="M20 14.4A8 8 0 1 1 9.6 4 6.5 6.5 0 0 0 20 14.4z" />
  </svg>
);

const Tag = ({ text, lang }) => (
  <span className={`tag t-${tone(text)}`}><i className="dot" />{tV(lang, text)}</span>
);

function AgentBlock({ decision, name, lang, L }) {
  if (!decision) return null;
  return (
    <div className="agent">
      <div className="a-head">
        <span className="a-name">{tAgent(lang, name)}</span>
        <Tag text={decision.verdict} lang={lang} />
        <span className="conf mono">{L.conf} {(decision.confidence || 0).toFixed(2)}</span>
      </div>
      <div className="rationale">{decision.rationale}</div>
      {(decision.evidence || []).map((e, i) => (
        <div key={i} className="ev">
          <span className="k">{e.kind}</span> · {e.detail}
          {e.weight ? <span className={`w mono ${e.weight > 0 ? "pos" : "neg"}`}> ({e.weight > 0 ? "+" : ""}{e.weight.toFixed(2)})</span> : null}
        </div>
      ))}
      {name === "responder" && decision.data && decision.data.draft ? (
        <>
          <div className="draft-label">{L.draft}</div>
          <div className="draft">{decision.data.draft}</div>
        </>
      ) : null}
    </div>
  );
}

function ItemRow({ r, lang, L }) {
  const [open, setOpen] = useState(false);
  const it = r.item;
  const tri = decisionOf(r, "triage") || {};
  const qual = decisionOf(r, "quality") || {};
  const slop = (qual.data && qual.data.slop_score) || 0;
  const labels = actionOf(r, "add_labels")?.payload.labels || [];
  const pri = (tri.data && tri.data.priority) || "-";
  const kindLabel = it.kind === "pull_request" ? "PR" : "issue";
  const applicable = qual.verdict && qual.verdict !== "not-applicable";
  const shown = ["triage", "quality", "reproducer", "responder"].map((a) => [a, decisionOf(r, a)]).filter(([, d]) => d);
  return (
    <div className={`item ${open ? "open" : ""}`}>
      <div className="row" onClick={() => setOpen(!open)}>
        <span className="num mono">#{it.number}</span>
        <span className="kind mono">{kindLabel}</span>
        <span className="title">{it.title}</span>
        <span className="meta">
          <span className={`pri mono ${pri === "high" ? "pri-high" : pri === "medium" ? "pri-med" : ""}`}>{tPri(lang, pri)}</span>
          <Tag text={tri.verdict || "-"} lang={lang} />
          {applicable ? (
            <>
              <Tag text={qual.verdict} lang={lang} />
              <span className={`meter t-${tone(qual.verdict)}`}><i style={{ width: Math.round(slop * 100) + "%" }} /></span>
              <span className="score mono">{slop}</span>
            </>
          ) : null}
          <span className="chev">&rsaquo;</span>
        </span>
      </div>
      {open ? (
        <div className="body">
          <div className="chips">
            {labels.map((l) => (<span key={l} className={`chip t-${tone(l)}`}><i className="dot" />{tV(lang, l)}</span>))}
          </div>
          {shown.map(([a, d]) => (<AgentBlock key={a} name={a} decision={d} lang={lang} L={L} />))}
          <div className="approval mono">{L.proposed}{r.actions.map((a) => a.type).join(", ")}</div>
        </div>
      ) : null}
    </div>
  );
}

const StatCell = ({ n, label, hot }) => (
  <div className={`stat ${hot && n > 0 ? "hot" : ""}`}><div className="n">{n}</div><div className="l">{label}</div></div>
);

function initialLang() {
  try { const s = localStorage.getItem("ma_lang"); if (s) return s; } catch (e) { /* ignore */ }
  return (navigator.language || "en").toLowerCase().startsWith("zh") ? "zh" : "en";
}
function initialTheme() {
  const attr = typeof document !== "undefined" && document.documentElement.getAttribute("data-theme");
  if (attr) return attr;
  return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  const [lang, setLangState] = useState(initialLang);
  const [theme, setTheme] = useState(initialTheme);
  const [repo, setRepo] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const L = I18N[lang];

  useEffect(() => { document.documentElement.setAttribute("data-theme", theme); }, [theme]);

  async function analyze(target, useLang) {
    const lg = useLang || lang;
    setError(""); setData(null); setRepo(target);
    try {
      const q = "?lang=" + lg + (target ? "&repo=" + encodeURIComponent(target) : "");
      const res = await fetch("/api/run" + q);
      if (!res.ok) throw new Error("HTTP " + res.status);
      setData(await res.json());
    } catch (e) { setError(String(e)); }
  }

  useEffect(() => { analyze("", lang); /* eslint-disable-next-line */ }, []);

  function setLang(next) {
    if (next === lang) return;
    setLangState(next);
    try { localStorage.setItem("ma_lang", next); } catch (e) { /* ignore */ }
    analyze(repo, next);
  }
  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    try { localStorage.setItem("ma_theme", next); } catch (e) { /* ignore */ }
  }

  const counts = data?.stats?.counts || {};
  const s = data?.stats;
  return (
    <div>
      <header>
        <div className="wrap">
          <div className="topbar">
            <div className="brand"><div className="mark">m</div><div className="wordmark">maintainer&#8209;agent</div></div>
            <div className="toggles">
              <button className="iconbtn" onClick={toggleTheme} aria-label="Toggle theme">
                {theme === "dark" ? <SunIcon /> : <MoonIcon />}
              </button>
              <div className="seg">
                <button className={lang === "en" ? "active" : ""} onClick={() => setLang("en")}>EN</button>
                <button className={lang === "zh" ? "active" : ""} onClick={() => setLang("zh")}>中文</button>
              </div>
            </div>
          </div>
          <p className="sub">{L.tagline}</p>
          <div className="controls">
            <input
              value={repo}
              placeholder={L.placeholder}
              onChange={(e) => setRepo(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") analyze(repo.trim()); }}
            />
            <button className="act" onClick={() => analyze(repo.trim())}>{L.analyze}</button>
            <button className="ghost" onClick={() => analyze("")}>{L.demo}</button>
            <span className="hint">{L.hint}</span>
          </div>
          <div className="status mono">
            {s ? (
              <>
                {L.st.source} <b>{data.offline ? "fixtures" : data.repo}</b> &nbsp; {L.st.backend} <b>{data.backend}</b>
                &nbsp; {L.st.llm} <b>{data.llm}</b> &nbsp; {L.st.run} <b>{data.run_id}</b> &nbsp; {data.count} {L.st.items}
              </>
            ) : "\u00a0"}
          </div>
        </div>
      </header>

      <main className="wrap">
        <div className="stats">
          <StatCell n={s?.total ?? 0} label={L.stat.reviewed} />
          <StatCell n={counts.attention || 0} label={L.stat.attention} hot />
          <StatCell n={counts.duplicates || 0} label={L.stat.duplicates} />
          <StatCell n={counts.ready || 0} label={L.stat.ready} />
          <StatCell n={counts.good_first || 0} label={L.stat.good_first} />
          <StatCell n={counts.more_info || 0} label={L.stat.more_info} />
        </div>
        <div className="cols">
          <section>
            <div className="col-title">{L.listTitle}</div>
            <div className="list">
              {error ? <div className="loading">{L.errPre}{error}{L.errSuf}</div> : null}
              {!data && !error ? <div className="loading">{repo ? L.loading : L.loadingDemo}</div> : null}
              {data ? data.results.map((r) => <ItemRow key={r.item.number} r={r} lang={lang} L={L} />) : null}
            </div>
          </section>
          <aside>
            <div className="panel">
              <h2>{L.digestTitle}</h2>
              <div className="md" dangerouslySetInnerHTML={{ __html: renderMarkdown(data?.digest_md) }} />
            </div>
          </aside>
        </div>
      </main>

      <footer className="wrap">
        {L.footer}
        <a href="https://github.com/0717lee/OSS-Maintainer-Assistant" target="_blank" rel="noopener">{L.source}</a>
      </footer>
    </div>
  );
}
