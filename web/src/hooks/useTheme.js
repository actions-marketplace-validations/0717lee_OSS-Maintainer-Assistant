import { useState, useEffect } from "react";

function initialTheme() {
  try {
    const stored = localStorage.getItem("ma_theme");
    if (stored) return stored;
  } catch (e) { /* ignore */ }
  if (typeof document !== "undefined") {
    const attr = document.documentElement.getAttribute("data-theme");
    if (attr) return attr;
  }
  return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function useTheme() {
  const [theme, setTheme] = useState(initialTheme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  function toggleTheme() {
    setTheme((prev) => {
      const next = prev === "dark" ? "light" : "dark";
      try { localStorage.setItem("ma_theme", next); } catch (e) { /* ignore */ }
      return next;
    });
  }

  return { theme, toggleTheme };
}
