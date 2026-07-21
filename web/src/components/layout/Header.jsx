import { Sun, Moon } from "lucide-react";
import { cn } from "../../lib/utils";

export function Header({ lang, setLang, theme, toggleTheme, L }) {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-[color-mix(in_srgb,var(--bg-base)_84%,transparent)] backdrop-blur-md backdrop-saturate-150">
      <div className="container-main">
        <div className="flex items-center justify-between gap-4 pt-5">
          <span className="font-mono text-[15px] font-semibold tracking-tight text-text-primary">
            maintainer<span className="font-medium text-text-tertiary">-agent</span>
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="grid h-[30px] w-[34px] place-items-center rounded-md border border-border-focus text-text-secondary transition-all duration-150 hover:bg-surface hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-weak"
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <div className="inline-flex overflow-hidden rounded-md border border-border-focus">
              {["en", "zh"].map((l) => (
                <button
                  key={l}
                  onClick={() => setLang(l)}
                  className={cn(
                    "border-0 px-2.5 py-[5px] text-xs font-semibold transition-all duration-150",
                    l === "en" ? "" : "border-l border-border-focus",
                    lang === l
                      ? "bg-accent text-canvas"
                      : "bg-transparent text-text-secondary hover:bg-surface hover:text-text-primary"
                  )}
                >
                  {l === "en" ? "EN" : "中文"}
                </button>
              ))}
            </div>
          </div>
        </div>
        <p className="mt-3.5 max-w-[60ch] text-sm text-text-secondary">{L.tagline}</p>
      </div>
    </header>
  );
}
