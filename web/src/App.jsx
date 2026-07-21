import { useState } from "react";
import { I18N } from "./lib/i18n";
import { useTheme } from "./hooks/useTheme";
import { useAnalysis } from "./hooks/useAnalysis";
import { Header } from "./components/layout/Header";
import { Footer } from "./components/layout/Footer";
import { RepoInput } from "./components/dashboard/RepoInput";
import { StatusLine } from "./components/dashboard/StatusLine";
import { StatsBar } from "./components/dashboard/StatsBar";
import { IssueList } from "./components/dashboard/IssueList";
import { DigestModal } from "./components/dashboard/DigestModal";
import { SkeletonStats } from "./components/dashboard/SkeletonList";

function initialLang() {
  try {
    const s = localStorage.getItem("ma_lang");
    if (s) return s;
  } catch (e) { /* ignore */ }
  return (navigator.language || "en").toLowerCase().startsWith("zh") ? "zh" : "en";
}

export default function App() {
  const [lang, setLangState] = useState(initialLang);
  const { theme, toggleTheme } = useTheme();
  const { repo, setRepo, data, error, loading, analyze } = useAnalysis(lang);
  const [digestOpen, setDigestOpen] = useState(false);
  const [filter, setFilter] = useState("all");
  const L = I18N[lang];

  function setLang(next) {
    if (next === lang) return;
    setLangState(next);
    try { localStorage.setItem("ma_lang", next); } catch (e) { /* ignore */ }
    // Don't re-run the pipeline on language switch — avoids rate limiting.
    // UI labels and verdict translations update client-side.
  }

  return (
    <div className="min-h-screen">
      <Header lang={lang} setLang={setLang} theme={theme} toggleTheme={toggleTheme} L={L} />

      <div className="container-main">
        <div className="pt-4">
          <RepoInput
            repo={repo}
            setRepo={setRepo}
            onAnalyze={(target) => analyze(target)}
            L={L}
          />
          <StatusLine data={data} L={L} />
        </div>
      </div>

      <main className="container-main pb-[72px]">
        {data || loading ? (
          <>
            {loading ? <SkeletonStats /> : <StatsBar stats={data?.stats} L={L} filter={filter} setFilter={setFilter} />}
            <IssueList
              data={data}
              error={error}
              loading={loading}
              repo={repo}
              lang={lang}
              L={L}
              filter={filter}
              onRetry={() => analyze(repo)}
              onOpenDigest={() => setDigestOpen(true)}
            />
          </>
        ) : (
          <IssueList
            data={data}
            error={error}
            loading={loading}
            repo={repo}
            lang={lang}
            L={L}
            onRetry={() => analyze(repo)}
            onOpenDigest={() => setDigestOpen(true)}
          />
        )}
      </main>

      <Footer L={L} />

      <DigestModal
        open={digestOpen}
        digestMd={data?.digest_md}
        L={L}
        onClose={() => setDigestOpen(false)}
      />
    </div>
  );
}
