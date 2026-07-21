import { useState, useCallback } from "react";

export function useAnalysis(lang) {
  const [repo, setRepo] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const analyze = useCallback(async (target, useLang) => {
    const lg = useLang || lang;
    setError("");
    setData(null);
    setLoading(true);
    setRepo(target);
    try {
      const q = "?lang=" + lg + (target ? "&repo=" + encodeURIComponent(target) : "");
      const res = await fetch("/api/run" + q);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      setData(await res.json());
    } catch (e) {
      setError(String(e).replace(/^Error:\s*/, ""));
    } finally {
      setLoading(false);
    }
  }, [lang]);

  return { repo, setRepo, data, error, loading, analyze };
}
