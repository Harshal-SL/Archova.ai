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
      className="relative flex h-8 w-8 items-center justify-center rounded-lg border border-neutral-200/80 bg-white/70 backdrop-blur-md text-neutral-800 shadow-xs transition-all hover:border-black hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-200 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white cursor-pointer"
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
