"use client";

import { useEffect } from "react";
import { Sun, Moon } from "lucide-react";
import { useAppStore } from "@/lib/store";

export default function ThemeToggle() {
  const { theme, toggleTheme, setTheme } = useAppStore();

  useEffect(() => {
    const saved = localStorage.getItem("theme") as "light" | "dark" | null;
    if (saved) setTheme(saved);
  }, [setTheme]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  return (
    <button
      onClick={toggleTheme}
      className="relative flex h-8 w-8 items-center justify-center rounded-lg border border-neutral-300 bg-white text-neutral-800 shadow-xs transition-all hover:border-black hover:text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:border-white dark:hover:text-white"
      aria-label="Toggle theme"
      title={theme === "dark" ? "Switch to Light Theme" : "Switch to Dark Theme"}
    >
      {theme === "dark" ? (
        <Sun className="h-4 w-4 text-white" />
      ) : (
        <Moon className="h-4 w-4 text-black" />
      )}
    </button>
  );
}
