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
      className="relative flex h-9 w-9 items-center justify-center rounded-full bg-gray-200 transition-colors hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600"
      aria-label="Toggle theme"
    >
      {theme === "dark" ? (
        <Sun className="h-4 w-4 text-yellow-400" />
      ) : (
        <Moon className="h-4 w-4 text-gray-700" />
      )}
    </button>
  );
}
